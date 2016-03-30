import binascii, sys

track_sizes = (0,
                21, 21, 21, 21, 21,
                21, 21, 21, 21, 21,
                21, 21, 21, 21, 21,
                21, 21, 19, 19, 19,
                19, 19, 19, 19, 18,
                18, 18, 18, 18, 18,
                17, 17, 17, 17, 17)
                
track_offsets = [0]
for i in xrange(35) :
    track_offsets.append(track_offsets[i] + track_sizes[i])

class D64image(object) :
    def __init__(self, image) :
        self.image = image
    
    def is_valid(self, track, sector) :
        if track < 1 or track > 35 :
            return False
        if sector < 0 or sector >= track_sizes[track] :
            return False
        return True
        
    def get_sector(self, track, sector) :
        if track < 1 or track > 35 :
            print "Invalid track!", track
            sys.exit()
        if sector < 0 or sector >= track_sizes[track] :
            print "Invalid sector!", track, sector
            sys.exit()
            
        sector_start = (track_offsets[track] + sector) * 256
        return self.image[sector_start:sector_start+256]

    def get_dir(self) :
        dir_entries = []
        
        track = 18
        sector = 1
        while True :
            sec = self.get_sector(track, sector)
            for i in xrange(0, 256, 32) :
                entry = sec[i:i+32]
                if ord(entry[2]) :
                    track = ord(entry[3])
                    sector = ord(entry[4])
                    filename = entry[5:21].rstrip("\xa0")
                    dir_entries.append((filename, track, sector))
            if ord(sec[0]) != 18 :
                break
            else :
                track = ord(sec[0])
                sector = ord(sec[1])
        
        return dir_entries
        
    def get_file_by_name(self, filename) :
        track = 0
        sector = 0
        
        dir = self.get_dir()
        for entry in dir :
            if filename == entry[0] :
                track = entry[1]
                sector = entry[2]
                break
        if track == 0 and sector == 0 :
            return ""
        else :
            return self.get_file_by_pos(track, sector)

    def get_file_by_pos(self, track, sector) :
        file = ""
        while True :
            sec = self.get_sector(track, sector)
            track = ord(sec[0])
            sector = ord(sec[1])
            if not self.is_valid(track, sector) :
                file += sec[2:2+sector-1]
                break
            else :
                file += sec[2:]
                
        return file