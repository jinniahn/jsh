import sys
from sys import exit
import os.path 
from tempfile import mkdtemp
from os import unlink, system, listdir, rmdir, getcwd, chdir

# adjust sys.path
sys.path.insert(0, '..')

from jsh import sh, sudo_sh, ssh_sh, ShellRunException

import unittest

class TestShell(unittest.TestCase):

    def setUp(self):
        self.tmpdir = mkdtemp()
        self.curdir = getcwd()
        chdir(self.tmpdir)
        for i in range(10):
            system('touch {}.txt'.format(i))

    def tearDown(self):
        for fname in listdir(self.tmpdir):
            unlink(os.path.join(self.tmpdir, fname))
        rmdir(self.tmpdir)
        chdir(self.curdir)

    def test_run_basic_shell(self):
        filelist = sh('ls', logfile=None).splitlines()
        self.assertEqual(len(filelist), 10)

    def test_run_with_evn(self):
        env = dict( PROGNAME = 'jsh_test')
        progname = sh('echo $PROGNAME', env=env, logfile=None).strip()
        self.assertEqual(progname , 'jsh_test')

    def test_interactive(self):
        chdir(self.curdir)
        
        input_events=[
            ('user_id:', 'jinsub ahn\n'),
            ('password:', 'password\n')
        ]    
    
        ret = sh('bash test/id_passwd.sh'
                 , input_events=input_events
                 , interactive=False
                 , logfile=None).splitlines()[-2:]

        self.assertEqual(ret[0], 'jinsub ahn')
        self.assertEqual(ret[1], 'password')

    def test_sudo_sh(self):
        input_events=[
            ('Password:', 'wrong_password\n'),
        ] * 10

        ret = sudo_sh('whoami'
                      , 'root'
                      , input_events=input_events
                      , logfile=None
                      , interactive=False ).splitlines()[-1]
        self.assertEqual(ret, 'sudo: 3 incorrect password attempts')


    @unittest.skip('')
    def test_ssh_cwd(self):
        cwd = '/usr'
        ret = ssh_sh('pwd', 'localhost', logfile=None, cwd=cwd).strip()
        self.assertEqual('/usr', ret)

    def test_exit_code(self):
        with self.assertRaises(ShellRunException):
            ret = sh('wrong_cmd', logfile=None)
            print(ret)

        print('xx');
        with self.assertRaises(ShellRunException):
            ret = ssh_sh('wrong_cmd', 'localhost', logfile=sys.stdout).strip()
            print(ret)

if __name__ == '__main__':
    unittest.main()
