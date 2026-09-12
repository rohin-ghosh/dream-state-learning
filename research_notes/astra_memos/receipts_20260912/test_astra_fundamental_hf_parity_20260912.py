"""CPU fixtures only: no torch/model dependency or GPU/subprocess calls."""
import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
import struct
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location("parity","/tmp/astra_fundamental_hf_parity_20260912.py")
parity=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)
parity.bind(Path.cwd())


class Tokenizer:
    eos_token_id=6
    pad_token_id=6
    def encode(self,text,add_special_tokens=False):
        colors={"red":2,"blue":3,"yellow":4,"green":5}
        return [colors[text]] if text in colors else [7]+[10+ord(char) for char in text]


class Tensor:
    def __init__(self,value,dtype="fp32"):
        self.value,self.dtype,self.shape=value,dtype,(8,16)
    def to(self,device,dtype):
        return Tensor(self.value,dtype)


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hf-parity-cpu-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.tok=Tokenizer()
        self.cases=parity.diagnostic.selected_cases()
        self.seq=dict(identity={"fixture":"identity"},requests=parity.diagnostic.requests(self.cases),native_inputs=[])
        self.items,self.captures=[],[]
        for case,request in zip(self.cases,self.seq["requests"]):
            rendered="USER: "+case["context"]+"\nASSISTANT:"
            prefix=self.tok.encode(rendered)
            self.seq["native_inputs"].append(dict(rendered_prompt=rendered,prompt_token_ids=prefix))
            self.items.append(dict(group=case["id"],view="memory",spans=[[rendered,False,"context"],
                [case["expected"],True,"authored_birth_target"]]))
            response=dict(text="red",rendered_prompt=rendered,prompt_token_ids=prefix,
                output_token_ids=[2,6],finish_reason="stop",stop_reason=None)
            self.captures.append((dict(request=request,identity=self.seq["identity"],
                prompt_sha256=parity.base.value_hash(request["prompt"])),
                dict(response=response,response_sha256=parity.base.value_hash(response))))

    def rows(self):
        return parity.build_rows(self.seq,self.cases,self.items,self.captures,self.tok)

    def test_exact16_native_prefix_and_inherited_outputs(self):
        rows=self.rows()
        self.assertEqual(len(rows),16)
        for row,capture in zip(rows,self.captures):
            self.assertEqual(row["vllm_response"],capture[1])
            self.assertEqual(row["vllm_request"],capture[0])
            self.assertEqual(row["prefix_ids"],capture[1]["response"]["prompt_token_ids"])
            self.assertEqual(row["labels"],[-100]*len(row["prefix_ids"])+[row["gold_id"],6])

    def test_changed_training_prefix_rejected(self):
        self.items[0]["spans"][0][0]+="hint"
        with self.assertRaisesRegex(ValueError,"context/target/mask"):
            self.rows()

    def test_actual_response_prefix_mismatch_rejected(self):
        self.captures[0][1]["response"]["prompt_token_ids"]=[]
        self.captures[0][1]["response_sha256"]=parity.base.value_hash(self.captures[0][1]["response"])
        with self.assertRaisesRegex(ValueError,"prefix mismatch"):
            self.rows()

    def test_raw_response_seal_rejected(self):
        self.captures[0][1]["response"]["text"]="blue"
        with self.assertRaisesRegex(ValueError,"seal changed"):
            self.rows()

    def test_changed_target_or_mask_rejected(self):
        self.items[0]["spans"][1][1]=False
        with self.assertRaisesRegex(ValueError,"context/target/mask"):
            self.rows()

    def test_missing_case_rejected(self):
        self.captures.pop()
        with self.assertRaisesRegex(ValueError,"exact16"):
            self.rows()

    def test_causal_indices_not_unshifted_target_indices(self):
        row=self.rows()[0]
        length=len(row["prefix_ids"])
        self.assertEqual(parity.positions(row),(length-1,length))
        row["color_position"]-=1
        with self.assertRaisesRegex(ValueError,"shift"):
            parity.positions(row)

    def test_eos_shift_and_label_corruption_rejected(self):
        row=self.rows()[0]
        row["labels"][len(row["prefix_ids"])-1]=row["gold_id"]
        with self.assertRaisesRegex(ValueError,"shift"):
            parity.positions(row)

    def test_logits_gold_eos_and_vllm_comparison(self):
        row=self.rows()[0]
        prefix=[0.]*10
        prefix[row["gold_id"]]=4.
        full=prefix.copy()
        eos=[0.]*10
        eos[6]=5.
        result=parity.metrics(row,[prefix,full,eos])
        self.assertEqual(result["prefix"]["top1_id"],row["gold_id"])
        self.assertFalse(result["top1_matches_vllm"])
        self.assertAlmostEqual(result["color_nll"],math.log(math.exp(4)+9)-4)
        self.assertAlmostEqual(result["eos_nll"],math.log(math.exp(5)+9)-5)
        self.assertEqual(result["prefix_full_max_abs_logit_difference"],0)

    def test_small_discrepancy_recorded_without_threshold(self):
        row=self.rows()[0]
        vectors=[[0.]*10 for _ in range(3)]
        vectors[1][row["gold_id"]]=1e-8
        result=parity.metrics(row,vectors)
        self.assertEqual(result["prefix_full_max_abs_logit_difference"],1e-8)
        self.assertNotIn("passed",result)

    def test_top1_is_not_closed_set_rescue(self):
        row=self.rows()[0]
        vectors=[[0.]*10 for _ in range(3)]
        vectors[0][9]=10
        vectors[0][row["gold_id"]]=5
        self.assertEqual(parity.metrics(row,vectors)["prefix"]["top1_id"],9)

    def test_nonfinite_or_bad_vocab_rejected(self):
        row=self.rows()[0]
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            parity.metrics(row,[[float("nan")]*10]*3)
        with self.assertRaisesRegex(ValueError,"vocabulary"):
            parity.metrics(row,[[0.]*2]*3)

    def test_loaded_all_tensor_inventory_and_conversion(self):
        def inventory(state):
            return {name:(tensor.value,tensor.dtype,tensor.shape) for name,tensor in state.items()}
        source={"layer.lora_A.weight":Tensor(1),"layer.lora_B.weight":Tensor(2)}
        loaded={name:tensor.to("cpu","bf16") for name,tensor in source.items()}
        with patch.object(parity.trainer,"_warm_validate_state",side_effect=lambda a,b:inventory(a)), \
            patch.object(parity.trainer,"_warm_state_inventory",side_effect=inventory):
            result=parity.loaded_state(source,loaded)
            self.assertTrue(result["exact_loaded_check"])
            self.assertEqual(len(result["dtype_conversions"]),2)
            loaded["layer.lora_B.weight"].value=3
            with self.assertRaisesRegex(ValueError,"loaded PEFT"):
                parity.loaded_state(source,loaded)

    def plan_fixture(self):
        adapter=self.root/"adapter"
        adapter.mkdir()
        (adapter/"weights-fixture").write_bytes(b"fixture")
        seqroot=self.root/"seq"
        seqroot.mkdir()
        plan=dict(label=parity.LABEL,source_root=str(parity.base.REPO),source_hashes=parity.sources(),
            model="fixture",model_files={"fixture":"hash"},adapter=str(adapter),
            adapter_files=parity.trainer._warm_inventory(adapter),seq100_root=str(seqroot),seq100_files={},
            seed0_inputs={},device="0",forwards=32,new_vllm_calls=0,optimizer_steps=0,dtype="bf16",
            worker_seconds=600,cleanup_reserve=140,rows=self.rows())
        parity.write(self.root/"plan.json",plan)
        parity.write(self.root/"plan.sha256.json",dict(sha256=parity.base.digest(self.root/"plan.json")))
        return plan

    def test_source_mismatch_rejected(self):
        self.plan_fixture()
        with patch.object(parity,"sources",return_value={"different":"source"}):
            with self.assertRaisesRegex(ValueError,"source changed"):
                parity.verify(self.root)

    def test_adapter_mismatch_rejected(self):
        plan=self.plan_fixture()
        (Path(plan["adapter"])/"weights-fixture").write_bytes(b"changed")
        with patch.object(parity.base,"model_hashes",return_value=plan["model_files"]):
            with self.assertRaisesRegex(ValueError,"model/adapter changed"):
                parity.verify(self.root)

    def test_plan_fixture_valid_without_native_models(self):
        plan=self.plan_fixture()
        with patch.object(parity.base,"model_hashes",return_value=plan["model_files"]):
            self.assertEqual(parity.verify(self.root),plan)

    def test_exclusive_paths_no_overwrite(self):
        self.plan_fixture()
        before=(self.root/"plan.json").read_bytes()
        with self.assertRaises(FileExistsError):
            parity.write(self.root/"plan.json",{})
        self.assertEqual((self.root/"plan.json").read_bytes(),before)
        with self.assertRaisesRegex(ValueError,"fresh"):
            parity.prepare(self.root,"unused","unused",0.)

    def test_worker_command_and_no_launch_without_authority(self):
        command=parity.worker_command(self.root)
        self.assertIn("_worker",command)
        self.assertIn("--source-root",command)
        self.assertIn("--allow-gpu",command)
        self.assertNotIn("vllm",str(command))
        with self.assertRaisesRegex(ValueError,"allocation"):
            parity.run(self.root)

    def output_fixture(self):
        plan=self.plan_fixture()
        data=self.root/"run"/"data"
        data.mkdir(parents=True)
        worker=self.root/"run"/"worker"
        worker.mkdir()
        parity.write(worker/"supervision.json",dict(returncode=0,ok=True,owned_group_empty=True,
            gpu_processes_absent=True,reservation_release_verified=True,reserved_seconds=1.))
        parity.write(data/"cleanup.json",dict(error=None,handle_released=True))
        parity.write(data/"load.json",dict(exact_loaded_check=True,loaded={"fixture":"state"},
            expected_after_dtype_conversion={"fixture":"state"},base_frozen=True,eval=True))
        parity.write(data/"state_after.json",{"fixture":"state"})
        for row in plan["rows"]:
            vectors=[[0.]*10 for _ in range(3)]
            result=parity.metrics(row,vectors)
            result.update(case_id=row["case_id"],hf_reported_loss=math.log(10),
                hf_loss_minus_recomputed=math.log(10)-result["full_response_mean_nll"],vocab_size=10,top1_text="fixture")
            parity.write(data/(row["case_id"]+".json"),result)
            (data/(row["case_id"]+".f32")).write_bytes(struct.pack("<30f",*([0.]*30)))
        parity.write(data/"manifest.json",dict(files=parity.base.tree_hashes(data),forwards=32))
        return plan,data

    def test_reduce_recomputes_all16_raw_logits_without_model(self):
        plan,data=self.output_fixture()
        with patch.object(parity.base,"model_hashes",return_value=plan["model_files"]):
            result=parity.reduce(self.root)
        self.assertTrue(result["complete"])
        self.assertEqual(result["total"],16)
        self.assertEqual(result["forwards"],32)
        self.assertEqual(result["new_vllm_calls"],0)

    def test_reduce_missing_artifact_not_zero(self):
        plan,data=self.output_fixture()
        (data/(plan["rows"][0]["case_id"]+".f32")).unlink()
        with patch.object(parity.base,"model_hashes",return_value=plan["model_files"]):
            with self.assertRaisesRegex(ValueError,"output bytes"):
                parity.reduce(self.root)

    def test_reduce_cleanup_failure_rejected(self):
        plan,data=self.output_fixture()
        path=self.root/"run"/"worker"/"supervision.json"
        value=parity.base.read(path)
        value["gpu_processes_absent"]=False
        path.write_text(parity.json.dumps(value))
        with patch.object(parity.base,"model_hashes",return_value=plan["model_files"]):
            with self.assertRaisesRegex(ValueError,"cleanup incomplete"):
                parity.reduce(self.root)

    def test_reduce_tampered_logits_rejected(self):
        plan,data=self.output_fixture()
        (data/(plan["rows"][0]["case_id"]+".f32")).write_bytes(struct.pack("<30f",*([1.]*30)))
        with patch.object(parity.base,"model_hashes",return_value=plan["model_files"]):
            with self.assertRaisesRegex(ValueError,"output bytes"):
                parity.reduce(self.root)


if __name__=="__main__":
    unittest.main()
