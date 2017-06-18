import subprocess

bb = subprocess.check_output('docker ps -aq -f status=paused -f status=exited -f status=dead -f status=created')
containers = [x for x in bb.split('\n') if x]
for container in containers:
    subprocess.check_call('docker rm -f %s' % container)



