#
# file to keep track of simple function

import os
import datetime
import re
from pyfaidx import Fasta


def exists(f):
    return(os.path.exists(f))


def log(m, verbose = True):
    ts = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    if verbose:
        print("{}: {}".format(ts, m))
        

def gmesBED(gtf, output):
    """
    given a gmes gtf it will extract ranges and write
    a bed line for each transcript
    """
    nre = re.compile(r'gene_id "([0-9]+_g)\";')
    beds = {}
    with open(gtf) as f:
        for line in f:
            if line.startswith("#"):
                continue
            
            l = line.split("\t")
            # regex match
            start = int(l[3])
            stop = int(l[4])
            
            name = (nre.findall(l[8]))[0]
            
            if name not in beds.keys():
                beds[name] = {"chrom": l[0],
                              "r": []}
            beds[name]['r'].append(start)
            beds[name]['r'].append(stop)
            
    #write to file
    with open(output, "w") as f:
        for name, v in beds.items():
            l = "\t".join([v['chrom'], str(min(v['r'])), str(max(v['r'])), ".", name])
            f.write("{}\n".format(l))
            
    return(output)
            
def readbed(bedfile):
    # read in bedfile
    bed = {}
    with open(bedfile) as b:
        for line in b:
            l = line.split()
            bed[l[4]] = {"chrom": l[0],
                         "start": int(l[1]), 
                         "stop": int(l[2]),
                         "strand": l[3]}
    return(bed)


def mergeOverlaps(intervals, dist = 0):
    '''https://codereview.stackexchange.com/a/69249'''
    sorted_by_lower_bound = sorted(intervals, key=lambda tup: tup[0])
    merged = []

    for higher in sorted_by_lower_bound:
        if not merged:
            merged.append(higher)
        else:
            lower = merged[-1]
            # test for intersection between lower and higher:
            # we know via sorting that lower[0] <= higher[0]
            if higher[0] <= (lower[1] + dist):
                upper_bound = max(lower[1], higher[1])
                merged[-1] = [lower[0], upper_bound]  # replace by merged interval
            else:
                merged.append(higher)

    return(merged)

def writeFasta(path, name, seq):
    with open(path, "w") as f:
        f.write(">{}\n{}\n".format(name, seq))
    return(path)



def readFasta(file):
    seqs = {}
    with open(file) as f:
        for line in f:
            if line.startswith(">"):
                name = line.strip()
                seqs[name] = ""
            else:
                seqs[name] += line.strip()
    return(seqs)


def readFastaNames(file):
    f = Fasta(file)
    return(list(f.keys()))
    #names = []
    #with open(file) as f:
    #    for line in f:
    #        if line.startswith(">"):
    #            names.append(line.strip())
    #        else:
    #            continue
    #return(names)

def horizontalConcat(output, files, profiles, sourcealignment):
    seqs = {}
    allnames = set()
    for profile, f in zip(profiles, files):
        #print("Reding {} {}".format(profile,f))
        seqs[profile] = readFasta(f)
        for name, seq in seqs[profile].items():
            allnames.add(name)
    
    # length matter
    # as I will need to pad single seqs
    lengths = {}
    for profile, seq in seqs.items():
        for k, s in seq.items():
            lengths[profile] = len(s)
            break
            
    # add names from source alignment to
    # the alignment, as this will make pplacer happy
    sa = readFastaNames(sourcealignment)
    sa = [">{}".format(s) for s in sa]
    allnames |= set(sa)
        
    
    # add missing seqences as strings of spaces
    for profile, seq in seqs.items():
        for name in allnames:
            if name not in seqs[profile].keys():
                seqs[profile][name] = "".join(lengths[profile] * ["-"])
            
    mergedSeqs = {}
    for name in allnames:
        s = ""
        for p in profiles:
            s += seqs[p][name]
        mergedSeqs[name] = s
    
    # write output:
    with open(output, "w") as f:
        for name, seq in mergedSeqs.items():
            seq = seq.replace(".", "-")
            f.write("{}\n{}\n".format(name, seq))
    
    return(output)

def concatenate(output, filenames, ungap = True):
    with open(output, 'w') as outfile:
        for fname in filenames:
            with open(fname) as infile:
                outfile.write(infile.read())
    return(output)


def readTSV(fp):
    res = []
    with open(fp) as f:
        cols = []
        for row in f:
            row = row.strip()
            l = row.split()
            if len(cols) == 0:
                cols = l
            else:
                n = {}
                for k,v in zip(cols, l):
                    n[k] = v
                res.append(n)
    return(res)

def readCSV(fp, sep = ","):
    res = []
    with open(fp) as f:
        cols = []
        for row in f:
            row = row.strip()
            l = row.split(",")
            if len(cols) == 0:
                cols = l
            else:
                n = {}
                for k,v in zip(cols, l):
                    n[k] = v
                res.append(n)
    return(res)

def clearFastaNames(fastaIn, fastaOut):
    nms = []
    with open(fastaOut, "w") as o:
        with open(fastaIn) as f:
            for line in f:
                if line.startswith(">"):
                    l = line.split()
                    N = l[0].strip()
                    n = N
                    i = 0
                    while n in nms:
                        n = "{}.{}".format(N ,i)
                        i += 1
                    o.write("{}\n".format(n))
                    nms.append(n)
                else:
                    o.write(line)
    return(fastaOut)