import urllib2

#url = "https://www.dropbox.com/s/g34dv4saey56nt6/Illiad%20ex?dl=1"
url = "https://www.dropbox.com/s/jvvh5a3wdwe7k3o/test?dl=1"
#url = "https://www.google"
u = urllib2.urlopen(url)
meta = u.info()
file_size = int(meta.getheaders("Content-Length")[0])
if file_size > 100000:
    pass
l = ""
file_size_dl = 0
block_sz = 8192
while True:
    buffer = u.read(block_sz)
    if not buffer:
        break

    l += buffer

l = l.splitlines()
#O(n^2) but readable
for i in list(l):
    stripped = i.strip(" ")
    if stripped == "":
        l.remove(i)
