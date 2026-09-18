import pytest

from gpu import orch_r136_node4_variants as variants
from gpu.orch_r136_node4_launch import BASE


def original_startup():
    base = str(BASE/'orch_r132_kernel_child_20260916_attempt1')
    return (base+'/workspace\n'+base+'/source1\nphysical 0 through the a40r wrapper\n'
        'After two generated segments, the runtime invites you to distill what you want to retain in a third segment, then sleeps.\n'
        'At sleep your nonempty distillation replaces the earlier visible history with your own summary.\n'
        '### Kernel environment\nAdd task\nThe current allocation ends no later than lease margin.')


@pytest.mark.parametrize('physical',[0,1,2,4,5,True,'3'])
def test_only_new_variant_lanes(physical):
    with pytest.raises(ValueError):
        variants.variant_plan({},physical)


def test_seed1_free_has_no_hidden_architecture_change():
    template = {'base_sha256':'frozen','decoder':{'temperature':0.7},'seed':0}
    result = variants.variant_plan(template,3)
    assert result['seed']==1 and result['presleep_variant']=='free_distillation'
    assert result['base_sha256']=='frozen' and result['decoder']==template['decoder']
    assert template['seed']==0


def test_reread_startup_truthfully_disclaims_extractiveness():
    text = variants.variant_startup(original_startup(),6,'/newlife','/newsource')
    assert 'prompt-guided selection' in text and 'not a machine-verified' in text
    assert 'with your own summary' not in text and 'lease margin' in text


def test_none_startup_no_longer_claims_third_generation_or_compaction():
    text = variants.variant_startup(original_startup(),7,'/newlife','/newsource')
    assert 'sleeps directly' in text and 'does not compact' in text
    assert 'third segment' not in text and 'with your own summary' not in text
    assert variants.variant_plan({},7)['compaction_invitation']==''


def test_seed1_startup_keeps_default_learning_and_actual_new_paths():
    text = variants.variant_startup(original_startup(),3,'/newlife','/newsource')
    assert 'in a third segment' in text and '/newlife/workspace' in text
    assert 'physical 3 through' in text and 'Socratic' in text
