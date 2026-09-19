PROGRAM = r'''
import errno,json,os,pathlib,select,sys,time

def process_start(pid):
    text=(pathlib.Path('/proc')/str(pid)/'stat').read_text()
    return int(text.rsplit(')',1)[1].split()[19])

def pidfd_exited(descriptor):
    poller=select.poll()
    poller.register(descriptor,select.POLLIN|select.POLLHUP|select.POLLERR)
    return bool(poller.poll(0))

def confirmed_exit(pid,descriptor,start):
    try: current=process_start(pid)
    except (FileNotFoundError,ProcessLookupError): current=None
    except OSError: return None
    if descriptor is not None:
        if pidfd_exited(descriptor) and (current is None or (start is not None and current==start)):
            return dict(pid=pid,start_ticks=start,current_start_ticks=current,proof='bound_pidfd_readable_no_new_lifetime')
        return None
    if current is not None: return None
    try:
        fresh=os.pidfd_open(pid,0)
    except ProcessLookupError:
        try: process_start(pid);return None
        except (FileNotFoundError,ProcessLookupError):
            return dict(pid=pid,start_ticks=start,proof='kernel_ESRCH_and_absent_start_after_enumeration')
        except OSError: return None
    except OSError: return None
    else:
        os.close(fresh)
        return None

def inspect_process(pid,identities,mapped):
    descriptor=None;start=None;writers=[];count=0
    try:
        start=process_start(pid)
        descriptor=os.pidfd_open(pid,0)
        if process_start(pid)!=start: raise ValueError('ProcessLifetimeChangedBeforeScan')
        process=pathlib.Path('/proc')/str(pid)
        directory=os.open(process/'fd',os.O_RDONLY|os.O_DIRECTORY)
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    info=entry.stat();count+=1
                    if (info.st_dev,info.st_ino) in identities:
                        fields=dict(line.split(':',1) for line in (process/'fdinfo'/entry.name).read_text().splitlines() if ':' in line)
                        mode=int(fields['flags'].strip(),8)&os.O_ACCMODE
                        if mode!=os.O_RDONLY: writers.append(dict(pid=pid,start_ticks=start,fd=int(entry.name),access_mode=mode))
        finally: os.close(directory)
        with (process/'maps').open('rb') as handle: maps=handle.read(2*1024*1024+1)
        if len(maps)>2*1024*1024: raise ValueError('MapsBoundExceeded')
        for line in maps.splitlines():
            fields=line.split(None,5)
            if len(fields)<5 or b'w' not in fields[1]: continue
            major,minor=fields[3].split(b':')
            if (int(major,16),int(minor,16),int(fields[4])) in mapped:
                writers.append(dict(pid=pid,start_ticks=start,kind='writable_mapping'))
        if process_start(pid)!=start: raise ValueError('ProcessLifetimeChangedAfterScan')
        if pidfd_exited(descriptor):
            proof=confirmed_exit(pid,descriptor,start)
            if proof is None: raise ValueError('UnresolvedExitOrPidReuse')
            return dict(writers=writers,verified_exit=proof,fds=count)
        return dict(writers=writers,fds=count)
    except (OSError,ValueError,KeyError) as error:
        proof=confirmed_exit(pid,descriptor,start)
        if proof is not None: return dict(writers=writers,verified_exit=proof,fds=count)
        return dict(writers=writers,fds=count,error=dict(pid=pid,start_ticks=start,error_type=type(error).__name__,reason=str(error) if isinstance(error,ValueError) else 'live_or_unresolved_process_unreadable'))
    finally:
        if descriptor is not None: os.close(descriptor)

def scan(paths):
    if os.geteuid()!=0 or not paths or len(paths)>40: raise ValueError('bounded_privileged_read_only_scan')
    identities={(pathlib.Path(path).stat().st_dev,pathlib.Path(path).stat().st_ino) for path in paths}
    mapped={(os.major(device),os.minor(device),inode) for device,inode in identities}
    result=dict(writers=[],inaccessible_or_exited=[],verified_exits=[],scanner_euid=os.geteuid(),scope='all_uid_privileged_fds_and_writable_maps',lifetime_protocol='pidfd_start_bound_v1',processes=0,fds=0)
    deadline=time.monotonic()+30
    for process in pathlib.Path('/proc').iterdir():
        if not process.name.isdigit(): continue
        if time.monotonic()>deadline:
            result['inaccessible_or_exited'].append(dict(error_type='ScanBoundExceeded'));break
        observed=inspect_process(int(process.name),identities,mapped)
        result['processes']+=1;result['fds']+=observed['fds']
        result['writers'].extend(observed['writers'])
        if 'error' in observed: result['inaccessible_or_exited'].append(observed['error'])
        if 'verified_exit' in observed: result['verified_exits'].append(observed['verified_exit'])
    return result

if __name__=='__main__':
    print(json.dumps(scan(json.load(sys.stdin)),sort_keys=True))
'''
