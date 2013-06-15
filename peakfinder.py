#! /usr/bin/python
# quick and dirty peakfinder for RTL-SDR by 0xabad1dea
# scans a range and reports signals found in mhz

# Tries very hard to not report those !@#$ phantom lines ---
# but as a result, avoid centering the window exactly on a
# frequency if you're specifically looking for it, as it may
# disappear or split into two.

# probably not very efficient

# BSD three-clause

# depends: https://github.com/roger-/pyrtlsdr


# fixme: narrow down the import... 
from pylab import *
from rtlsdr import *

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.4e6
# lower the gain to, like, 4 if you don't want to hear about weak signals
sdr.gain = 19

	
########################################################################
def peakdet(v, delta, x = None):
# hacked up from https://gist.github.com/endolith/250860
    maxtab = []
           
    if x is None:
        x = arange(len(v))
    
    v = asarray(v)
    
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN
    
    lookformax = True
    
    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mx = this
                mxpos = x[i]
                lookformax = True
 
    return array(maxtab)

########################################################################

def findsignals(candidates):
# input and output as [ [strength, strength, strength], [freq, freq, freq] ]
	sigdelta = 0.08 # adjacent peaks closer than this are collated

	# remove the center false spike before analysis
	cf = sdr.center_freq / 1e6

	# there's probably a more pythonic way to do this
	# but I'm just a humble C programmer
	for i in range(len(candidates[1])):
		if candidates[1][i] > (cf - (sigdelta/2)) and candidates[1][i] < (cf + (sigdelta/2)) :
			candidates[0][i] = 0.0
			
	# find local peaks
	max = peakdet(candidates[0],.0001) # empirical - adjust as desired
	# (make it smaller if you're looking for faint, wide signals)

	signals = []
	prevfreq = 0.0

	# collate adjacent peaks
	for i in max:
		if candidates[1][i[0]] - prevfreq < sigdelta:
			# leans right rather than left
			# (a cool person would perfectly center it?)
			del(signals[-1])
		signals.append([i[1], candidates[1][i[0]]])
		prevfreq = candidates[1][i[0]]
		
	return signals
		
########################################################################

signals = []

if len(sys.argv) != 3:
	exit("usage: peakfinder.py 88.0 110.0")

start = float(sys.argv[1])
end = float(sys.argv[2])
if start <= 0 or end <= 0:
	exit("error: bad arguments")

if end < start:
	exit("error: end < start")

freq = start

while(freq <= end):
	sdr.center_freq = freq * 1e6
	freq += 2.2 # this number was picked empirically to avoid overlap on my device
	samples = sdr.read_samples(256*1024)
	# plot the spectrum
	results = psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)

	signals.extend(findsignals(results))
	

# print just the frequency part 
print "++++++++++"
for i in signals:
	print "%.2f" % i[1]
print "++++++++++"



