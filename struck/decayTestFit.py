
import math
import ROOT


graph = ROOT.TGraphErrors()
random_generator = ROOT.TRandom3()
canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()
tau_hist = ROOT.TH1D("tau_hist","",200,0,2000)

fit_start = 20.0 # microseconds
decay_time_microseconds = 400.0
sampling_period_ns = 40.0
event_time = 17.0 # microseconds

noise = 20.0 # keV
baseline = 200.0 # keV
baseline = 0.0 # keV
energy_keV = 500.0

do_draw_fit = False
do_draw_fit = True

print "---> input values:"
print "\t baseline: [keV]", baseline
print "\t event_time: [microseconds]", event_time
print "\t sampling_period_ns:", sampling_period_ns
print "\t noise: [keV]", noise
print "\t energy_keV: [keV]", energy_keV
print "\t decay_time_microseconds:", decay_time_microseconds


for i_event in xrange(1000):

    print "--> event", i_event

    # make the wfm
    for i in xrange(800):
        y = random_generator.Gaus(baseline, noise)
        t = i*sampling_period_ns/1e3
        if t > event_time:
            y += energy_keV*math.exp(-(t-event_time)/decay_time_microseconds)

        graph.SetPoint(i,t,y)
        graph.SetPointError(i, 0, noise)

    baseline_guess = graph.GetY()[0]
    energy_guess = graph.GetY()[int(fit_start/sampling_period_ns*1e3)] - baseline_guess
    tau_guess = 150.0

    if do_draw_fit:
        print "---> par guesses:"
        print "\t baseline_guess:", baseline_guess
        print "\t energy_guess:", energy_guess
        print "\t tau_guess:", tau_guess


    fit_formula = "[1]*exp(-(x-%.1f)/[0])" % fit_start
    if baseline != 0:
        fit_formula = "[1]*exp(-(x-%.1f)/[0]) + [2]" % fit_start
    if do_draw_fit: 
        print "\t fit_formula:", fit_formula

    fcn = ROOT.TF1("fcn", fit_formula, fit_start, 32)
    fcn.SetLineColor(ROOT.kRed)
    fcn.SetLineWidth(2)

    # parameter guesses
    fcn.SetParameter(0, tau_guess)
    fcn.SetParameter(1, energy_guess)

    # error estimates
    fcn.SetParError(0, tau_guess*0.5)
    fcn.SetParError(1, noise)

    # names
    fcn.SetParName(0, "tau")
    fcn.SetParName(1, "energy")

    if baseline != 0:
        fcn.SetParameter(2, baseline_guess)
        fcn.SetParError(2, noise)
        fcn.SetParName(2, "baseline")

    fit_options = "WBRS"
    if not do_draw_fit: fit_options += "Q"
    fit_result = graph.Fit(fcn, fit_options)

    if do_draw_fit:
        graph.Draw("alx")
        hist = graph.GetHistogram()
        hist.SetXTitle("time [#mus]")
        hist.SetYTitle("Energy [keV]")
        fcn.Draw("same")
        canvas.Update()
        val = raw_input("--> enter to contiue (b=batch) ")
        if val == 'b':
            do_draw_fit = False


    fit_tau = fcn.GetParameter(0)
    tau_hist.Fill(fit_tau)

tau_hist.SetLineColor(ROOT.kBlue+1)
tau_hist.SetFillColor(ROOT.kBlue+1)
title = "%i fits: true #tau = %.1f #mus, fit mean: %.1f #mus" %(
    tau_hist.GetEntries(), decay_time_microseconds, tau_hist.GetMean())
tau_hist.SetTitle(title)
tau_hist.Draw()
canvas.Update()
canvas.Print("baseline_%i.pdf" % baseline)
print "hist mean:", tau_hist.GetMean()
print "decay_time_microseconds:", decay_time_microseconds
raw_input("--> enter to contiue... ")



