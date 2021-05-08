# -*- coding:utf-8 -*-

'''\
쉘프로그램 런너
===============

쉘프로그램을 파이썬에서 실행시키고 결과를 리턴해서 분석 받을 수
있도록 도와주는 API들

by Jinsub Ahn

사용법:
로드:
>>> import jsh

일반적인 쉘실행

>>> print(jsh.sh('ls'))

쉘에서 사용하는 파이프도 동일하게 사용할 수 있다

>>> print(jsh.sh('ls | wc -l'))

쉘에서 출력되는 로그를 확인한다.

>>> jsh.sh('ls /', logfile=sys.stdout)

쉘에서 출력되는 실행 파일을 실시간으로 분석할 수 있다



'''

import sys
import types
import subprocess
import fcntl
import os
import os.path
import time
from tempfile import NamedTemporaryFile
from pexpect import TIMEOUT, spawn, EOF

class ShellRunException(Exception):
    def __init__(self, log):
        Exception.__init__(self)
        self.log = log

__all__ = ['sh', 'sudo_sh', 'ssh_sh']

# global options
default_logfile = sys.stdout
dry_run = False

def escape_shell_cmd(text):
    text = text.replace(r'\\', r'\\\\')\
               .replace('"', r'\"')\
               .replace("$",r'\$')
    return text

def s(cmd, encoding='utf-8', logfile=sys.stdout, env=None, cwd=None):
    '''simple run process with nonblock i/o.
    '''

    if dry_run:
        print('{} {}'.format(shell, ' '.join(args)))
        return
    
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, env=env, cwd=cwd)

    # 파이프의 속성 값을 논블럭으로 설정
    fd = p.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    ## comment out because error below code
    fd = p.stderr.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    # 프로세스가 종료할때까지 주기적으로 읽는다.
    count = 3
    ret = []
    while(True):
        data = p.stdout.read() or p.stderr.read()
        if data:
            data = data.decode(encoding)
            if logfile:
                logfile.write(data)
            # add to buffer
            ret.append(data)
        else:
            # repeat every 0.2 sec
            time.sleep(0.2)            
        # 프로세스가 종료되었는지 확인
        if p.poll() != None:
            if count == 0:
                break;
            count -= 1

    # close pipe
    p.stderr.close()
    p.stdout.close()

    if logfile and logfile is not sys.stdout:
        logfile.close()

    if p.returncode != 0:
        raise ShellRunException(''.join(ret))
    
    return ''.join(ret)

def _run_cmd(cmd, args=[], logfile=sys.stdout, input_events=[], cwd=None, env=None, interactive=False):

    class DummyOutput(object):
        def __init__(self, outfile):
            self.outfile = outfile

        def write(self,data):
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            self.outfile.write(data)
        def flush(self):
            self.outfile.flush()

    if logfile:
        dummy_output = DummyOutput(logfile)
        logfile = dummy_output

    if dry_run:
        print('{} {}'.format(cmd, ' '.join(args)))
        if len(args) > 0 and os.path.exists(args[0]): 
            with open(args[0],'r') as f:
                print(f.read())
        sys.exit(0)

    def timeout_handler(d):
        pass

    events=[ (TIMEOUT, timeout_handler) ]
    events += input_events

    child = spawn(cmd, args, timeout=30, maxread=2000, logfile=logfile,
                  cwd=cwd, env=env, encoding='utf-8')
    if isinstance(events, list):
        patterns= [x for x,y in events]
        responses = [y for x,y in events]
    else:
        # This assumes EOF or TIMEOUT will eventually cause run to terminate.
        patterns = None
        responses = None

    child_result_list = []
    event_count = 0
    while True:
        try:
            if len(list(filter(lambda x: x != TIMEOUT, patterns))) == 0 and interactive:
                # turn on interactive function
                origin_logfile = child.logfile
                if child.logfile and child.logfile.outfile == sys.stdout:
                    child.logfile = None
                child.interact()
                child.logfile = origin_logfile
                interactive = False
            index = child.expect(patterns)
            if isinstance(child.after, child.allowed_string_types):
                child_result_list.append(child.before + child.after)
            else:
                # child.after may have been a TIMEOUT or EOF,
                # which we don't want appended to the list.
                child_result_list.append(child.before)
            if isinstance(responses[index], child.allowed_string_types):
                child.send(responses[index])
                # remove input event
                # assume all inputs cosume once
                del patterns[index]
                del responses[index]
            elif (isinstance(responses[index], types.FunctionType) or
                  isinstance(responses[index], types.MethodType)):
                callback_result = responses[index](locals())
                sys.stdout.flush()
                if isinstance(callback_result, child.allowed_string_types):
                    child.send(callback_result)
                elif callback_result:
                    break
                del patterns[index]
                del responses[index]
                
            else:
                raise TypeError("parameter `event' at index {index} must be "
                                "a string, method, or function: {value!r}"
                                .format(index=index, value=responses[index]))
            event_count = event_count + 1
        except TIMEOUT:
            #print('timeout')
            child_result_list.append(child.before)
            break
        except EOF:
            child_result_list.append(child.before)
            break
        except KeyboardInterrupt:
            child.close()

        except Exception as e:
            print(e)
            
    child_result = child.string_type().join(child_result_list)
    child.close()
    return child_result    

def sh(cmd, env=None, cwd=None, logfile=default_logfile, input_events=[], interactive=False, noshell=False):
    with NamedTemporaryFile('w', encoding="utf-8") as f:
        f.write(cmd)
        f.flush()

        if not input_events and not interactive:
            if logfile == None:
                return subprocess.check_output(cmd, env = env, cwd=cwd, shell=not noshell).decode('utf8')
            else:
                return s(['bash', f.name], env = env, cwd=cwd, logfile=logfile)
        else:
            return _run_cmd(cmd='bash', args = [f.name], env = env, cwd=cwd
                            , logfile = logfile, input_events= input_events
                            , interactive=interactive)
            

def sudo_sh(cmd, as_user, env=None, cwd='.', logfile=default_logfile, input_events=[], interactive=False):
    with NamedTemporaryFile('w', encoding="utf-8") as f:
        os.chmod(f.name, 0o777)
        f.write(cmd)
        f.flush()
        if not input_events and not interactive:
            return s(['sudo', '-H', '-u', as_user, 'bash', '-login', f.name], env = env, cwd=cwd, logfile=logfile)
        else:
            return _run_cmd(cmd='sudo', args = ['-H', '-u', as_user, 'bash', '-login', f.name], env = env, cwd=cwd
                            , logfile = logfile, input_events= input_events
                            , interactive=interactive)


def ssh_sh(cmd, remote_server, env=None, cwd=None, logfile=default_logfile, input_events=[], interactive=False):

    with NamedTemporaryFile('w', encoding="utf-8", delete=True) as f:
        #os.chmod(f.name, 0o777)
        # create command script
        if( cwd ) :
            print("cd '{}'".format(cwd), file=f)
        print(cmd, file=f)
        f.flush()
        cmd_file = f.name

        with NamedTemporaryFile('w', encoding="utf-8", delete=True) as f:
            #os.chmod(f.name, 0o777)
            # create ssh command script
            ssh_script_cmd = 'cat {} | ssh {} "f=\`mktemp\`; cat >> \$f; bash -login \$f; "'.format(cmd_file, remote_server)
            #print(ssh_script_cmd)
            f.write(ssh_script_cmd)
            f.flush()

            if not input_events and not interactive:
                return s(['bash', f.name], env = env, logfile=logfile)
            else:
                return _run_cmd(cmd='bash', args = [f.name], env = env, cwd=cwd
                                , logfile = logfile, input_events= input_events
                                , interactive=interactive)

