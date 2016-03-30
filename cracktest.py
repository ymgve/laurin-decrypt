import sys, binascii, struct, cStringIO

from d64 import D64image

def get_candidates(rom, offset):
    cands = {}
    for i in xrange(256):
        cands[ord(rom[offset + i])] = True
        
    return sorted(cands.keys())
    
def decrypt_byte(key, c):
    c = (c - key[0]) & 0xff
    c = c ^ key[1]
    c = (c - key[2]) & 0xff
    c = c ^ key[3]
    return c

def decrypt_block(key, s):
    s2 = ""
    for c in s:
        s2 += chr(decrypt_byte(key, ord(c)))
        
    return s2
    
def uncompress_block(s):
    cbyte, end, t, dest = struct.unpack("<BHHH", s[0:7])

    cs = cStringIO.StringIO (s[7:][::-1])

    s2 = ""
    while True:
        c = cs.read(1)
        if len(c) == 0:
            break
        if ord(c) != cbyte:
            s2 += c
        else:
            size = ord(cs.read(1))
            if size == 0:
                s2 += chr(cbyte)
            else:
                s2 += size * cs.read(1)
                
    s2 = s2[::-1]
    return s2

def test_key(key, ctext):
    if decrypt_byte(key, ord(ctext[3])) != 0:
        return False
    
    if decrypt_byte(key, ord(ctext[7])) != 0x12: # dir track number, almost 100% reliable
        return False
        
    if decrypt_byte(key, ord(ctext[8])) != 1: # dir sector number, almost 100% reliable
        return False

    if decrypt_byte(key, ord(ctext[9])) not in (0,0x41): # DOS
        return False

    if decrypt_byte(key, ord(ctext[6])) != 0x18: # decompression address, might not be constant
        return False
        
    if decrypt_byte(key, ord(ctext[4])) != 0x2b: # decompression address, might not be constant
        return False
        
    s = uncompress_block(decrypt_block(key, ctext))
    if len(s) < 0x1200 or len(s) > 0x1300:
        return False
        
    return True
    
basicrom = open("basic-ROM", "rb").read()
    
rawimg = open(sys.argv[1], "rb").read()
img = D64image(rawimg)

sector = img.get_sector(18, 0)
if sector[3] != "\x69":
    print "Not a valid Laurin image?"
    exit()

secnum = 6
ctext = ""
for i in xrange(15):
    ctext += img.get_sector(18, secnum)
    secnum = (secnum + 6) % 19

if ctext[3] != ctext[5] or ctext[3] != ctext[-1]:
    print "ambiguous zero"
    exit()
    
ctext = ctext.rstrip(ctext[-1]) # remove zeroes at the end of data

key0cands = get_candidates(basicrom, 0x336)
key1cands = get_candidates(basicrom, 0x783)
key2cands = get_candidates(basicrom, 0x1269)
key3cands = get_candidates(basicrom, 0x12a)

cands2 = {}
cands = []
src = ord(sector[2])
for a in key0cands:
    for b in key1cands:
        for c in key2cands:
            t = (src - a) & 0xff
            t = t ^ b
            t = (t - c) & 0xff
            t = t ^ 0x23
            key = (a,b,c,t)
            if t in key3cands and test_key(key, ctext):
                print binascii.b2a_hex(decrypt_block(key, ctext[0:16])), key
                cands.append(key)
                
                s = ""
                for i in xrange(256):
                    s += chr(decrypt_byte(key, i))
                if s not in cands2:
                    cands2[s] = True
                    s = uncompress_block(decrypt_block(key, ctext))
                    s = s.ljust(0x1300, "\x00")
                    s2 = [None] * 19
                    sid = 0
                    for i in xrange(19):
                        s2[sid] = s[i*0x100:i*0x100+0x100]
                        sid = (sid + 6) % 19
                        
                    s2 = "".join(s2)
                    
                    newimg = rawimg[:0x16500] + s2 + rawimg[0x17800:]
                    open(sys.argv[1] + ("_decrypted_%02x%02x%02x%02x.d64" % key), "wb").write(newimg)
            
print len(cands)
print len(cands2)

# print (162, 35, 0, 32) in cands


for i in xrange(0, len(ctext), 16):
    print "%08x" % i, binascii.b2a_hex(ctext[i:i+16]), repr(ctext[i:i+16])
