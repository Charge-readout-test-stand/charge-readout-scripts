"""
This file defines some useful analysis cuts to be used with tier3 files. 
"""

import math
import struck_analysis_parameters


def get_corrected_energy_cmd(
    energy_var="energy1_pz",
    max_drift_time=struck_analysis_parameters.max_drift_time,
):
    """
    Make a z correction to charge energy
    """
    return "energy1_pz*(1-(%s-x)*.01/(%s-%s))" % (
        max_drift_time,
        max_drift_time,
        struck_analysis_parameters.drift_time_threshold,
    )


def get_negative_energy_cut(threshold=-20.0, isMC=False):
    """
    return a cut on events with too much negative energy on any one channel
    """

    selection = []
    if isMC:
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    else:
        charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    for channel, value  in enumerate(charge_channels_to_use): 
        if value:
            cut = "(energy1_pz[%i]<%s)" % (
                channel, 
                threshold,
            )
            #print cut
            selection.append(cut)
            
    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses and add not
    selection = "(!(%s))" % selection

    return selection



def get_drift_time_selection(
    energy_threshold=200.0,
    drift_time_low=struck_analysis_parameters.drift_time_threshold,
    drift_time_high=None,
    isMC=False,
    is_single_channel=False,
):
    """
    KEEP -- Select events with energy above threshold and long enough drift time
    """

    if is_single_channel:
        selection = []
        if drift_time_low != None:
            selection.append("(rise_time_stop95-trigger_time>%s)" % drift_time_low)
        if drift_time_high != None:
            selection.append("(rise_time_stop95-trigger_time<%s)" % drift_time_high)
        selection = " && ".join(selection)
        return selection


    selection = []
    if isMC:
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    else:
        charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    for channel, value  in enumerate(charge_channels_to_use): 
        if value:
            cut = []
            cut2 = []
            if drift_time_low != None:
                cut1 = []
                if energy_threshold != None:
                    part = "(energy1_pz[%i]>%s)" % (
                        channel, 
                        energy_threshold,
                    )
                    cut1.append(part)
                part = "(rise_time_stop95[%i]-trigger_time>%s)" % (
                    channel, 
                    drift_time_low,
                )
                cut1.append(part)
                cut.append("&&".join(cut1))
            if drift_time_high != None:
                cut2 = []
                if energy_threshold != None:
                    part = "(energy1_pz[%i]>%s)" % (
                        channel, 
                        energy_threshold,
                    )
                    cut2.append(part)
                part = "(rise_time_stop95[%i]-trigger_time<%s)" % (
                    channel,
                    drift_time_high,
                )
                cut2.append(part)
                cut.append("&&".join(cut2))
            #print cut
            cut = "&&".join(cut)
            selection.append(cut)
            
    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses
    selection = "(%s)" % selection

    return selection





def get_drift_time_cut(
    energy_threshold=200.0,
    drift_time_low=struck_analysis_parameters.drift_time_threshold,
    drift_time_high=None,
    isMC=False,
    is_single_channel=False,
):
    """
    Select events with energy above threshold and long enough drift time
    """

    if is_single_channel:
        selection = []
        if drift_time_low != None:
            selection.append("!(rise_time_stop95-trigger_time<%s)" % drift_time_low)
        if drift_time_high != None:
            selection.append("!(rise_time_stop95-trigger_time>%s)" % drift_time_high)
        selection = " && ".join(selection)
        return selection

    selection = []
    #if struck_analysis_parameters.is_8th_LXe:
    if drift_time_low != None:
        selection.append("rise_time_stop95_sum-trigger_time < %s" % drift_time_low)
    if drift_time_high != None:
        selection.append("rise_time_stop95_sum-trigger_time > %s" % drift_time_high)
    

    #else:
    #    if isMC:
    #        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    #    else:
    #        charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    #    for channel, value  in enumerate(charge_channels_to_use): 
    #        if value:
    #            cut = []
    #            cut2 = []
    #            if drift_time_low != None:
    #                cut1 = []
    #                if energy_threshold != None:
    #                    part = "(energy1_pz[%i]>%s)" % (
    #                        channel, 
    #                        energy_threshold,
    #                    )
    #                    cut1.append(part)
    #                part = "(rise_time_stop95[%i]-trigger_time<%s)" % (
    #                    channel, 
    #                    drift_time_low,
    #                )
    #                cut1.append(part)
    #                cut.append("&&".join(cut1))
    #            if drift_time_high != None:
    #                cut2 = []
    #                if energy_threshold != None:
    #                    part = "(energy1_pz[%i]>%s)" % (
    #                        channel, 
    #                        energy_threshold,
    #                    )
    #                    cut2.append(part)
    #                part = "(rise_time_stop95[%i]-trigger_time>%s)" % (
    #                    channel,
    #                    drift_time_high,
    #                )
    #                cut2.append(part)
    #                cut.append("&&".join(cut2))
    #            #print cut
    #            cut = "||".join(cut)
    #            selection.append(cut)
                
    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses
    selection = "(!(%s))" % selection

    return selection

def get_chargeEnergy_no_pz():
    """A draw command for total energy before PZ correction """
    draw_cmd = []
    for channel, value in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            draw_cmd.append("energy1[%i]" % channel)
    # join each part with "+"
    draw_cmd = " + ".join(draw_cmd)
    return draw_cmd

def get_multiplicity_cmd(
    energy_var="energy1_pz",
    n_sigma=5.0, 
    energy_threshold=100.0,
    isMC=False
):
    """A draw command for multiplicity """
    if n_sigma==5.0:
        draw_cmd = "nsignals"
    else:
        draw_cmd = []
        if isMC:
            charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
        else:
            charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
        for channel, value in enumerate(charge_channels_to_use): 
            if value:
                #part = "(energy1_pz[%i]>%s)" % (channel,energy_threshold)
                if energy_threshold != 100.0: 
                    print "get_multiplicity_cmd: energy_threshold no longer used!"
                part = "(%s[%i]>%s*baseline_rms[%i]*calibration[%i]*%f)" % (
                    energy_var,
                    channel, 
                    n_sigma,
                    channel, 
                    channel, 
                    math.sqrt(2.0/struck_analysis_parameters.n_baseline_samples),
                )
                draw_cmd.append(part)

        # join each part with "+"
        draw_cmd = "+".join(draw_cmd)
    return draw_cmd

def get_single_strip_cut(n_sigma=5.0, isMC=False):
    """Select events with only one channel above threshold"""
    selection = "(%s==1)" % get_multiplicity_cmd(n_sigma=n_sigma, isMC=isMC)
    return selection

def get_few_one_strip_channels(
    n_sigma=5.0,
    energy_var="energy1_pz",
):
    """A draw command for total energy, only including single-strip channels above threshold """
    draw_cmd = []
    for channel, value in enumerate(struck_analysis_parameters.one_strip_channels): 
        if value:
            part = "(%s[%i]>%s*baseline_rms[%i]*calibration[%i]*%f)*%s[%i]" % (
                energy_var,
                channel, 
                n_sigma,
                channel, 
                channel, 
                math.sqrt(2.0/struck_analysis_parameters.n_baseline_samples),
                energy_var,
                channel,
            )

            draw_cmd.append(part)
    # join each part with "+"
    draw_cmd = " + ".join(draw_cmd)
    return draw_cmd

def get_few_two_strip_channels(
    n_sigma=5.0,
    energy_var="energy1_pz",
):
    """A draw command for total energy, only including single-strip channels above threshold """
    draw_cmd = []
    for channel, value in enumerate(struck_analysis_parameters.two_strip_channels): 
        if value:
            part = "(%s[%i]>%s*baseline_rms[%i]*calibration[%i]*%f)*%s[%i]" % (
                energy_var,
                channel, 
                n_sigma,
                channel, 
                channel, 
                math.sqrt(2.0/struck_analysis_parameters.n_baseline_samples),
                energy_var,
                channel,
            )

            draw_cmd.append(part)
    # join each part with "+"
    draw_cmd = " + ".join(draw_cmd)
    return draw_cmd


def get_few_channels_cmd(
    energy_threshold=10.0,
    energy_var="energy1_pz",
):
    """ A draw command for total energy, only including  events above threshold """
    draw_cmd = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            part = "(%s[%i]>%s)*%s[%i]" % (
                energy_var,
                channel, 
                energy_threshold,
                energy_var,
                channel,
            )
            #print part
            draw_cmd.append(part)
    # join each channel requirement with or
    draw_cmd = " + ".join(draw_cmd)
    return draw_cmd

def get_few_channels_cmd_rms_keV(
    n_sigma=5.0,
    energy_var="energy1_pz",
):
    """ A draw command for total energy, only including  events above threshold """
    draw_cmd = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            part = "(%s[%i]>%s*%s)*%s[%i]" % (
                energy_var,
                channel, 
                n_sigma,
                struck_analysis_parameters.rms_keV[channel]*math.sqrt(
                  2.0/struck_analysis_parameters.n_baseline_samples),
                energy_var,
                channel,
            )
            #print part
            draw_cmd.append(part)
    # join each channel requirement with or
    draw_cmd = " + ".join(draw_cmd)
    return draw_cmd

def get_few_channels_cmd_baseline_rms(
    n_sigma=5.0,
    energy_var="energy1_pz",
):
    """ A draw command for total energy, only including  events above threshold """
    draw_cmd = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            part = "(%s[%i]>%s*baseline_rms[%i]*calibration[%i]*%f)*%s[%i]" % (
                energy_var,
                channel, 
                n_sigma,
                channel, 
                channel, 
                math.sqrt(2.0/struck_analysis_parameters.n_baseline_samples),
                energy_var,
                channel,
            )
            #print part
            draw_cmd.append(part)
    # join each channel requirement with or
    draw_cmd = " + ".join(draw_cmd)
    return draw_cmd



def get_fiducial_cut(energy_threshold=100):
    selection = []
    selection.append("(energy1_pz[0]<%s)" % energy_threshold)
    selection.append("(energy1_pz[3]<%s)" % energy_threshold)
    selection.append("(energy1_pz[4]<%s)" % energy_threshold)
    selection.append("(energy1_pz[7]<%s)" % energy_threshold)
    return "&&".join(selection)


def get_cuts_label(draw_cmd, selection):

    label = []

    # check draw command
    if get_few_channels_cmd() in draw_cmd:
        label.append("FC")
    if get_chargeEnergy_no_pz() in draw_cmd:
        label.append("NPZ")

    # check selection
    if get_negative_energy_cut() in selection:
        label.append("NC")
    if get_drift_time_cut() in selection:
        label.append("LC")
    label = "+".join(label)
    if label == "": label = "No_cuts"
    return label

def get_energy_weighted_drift_time():
    selection = []

    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            cut = "energy1_pz[%i]*(rise_time_stop95[%i]-trigger_time)" % (
                channel, 
                channel, 
            )
            selection.append(cut)
    selection = " + ".join(selection)
    selection = "(%s)/chargeEnergy" % selection
    return selection



def get_channel_selection(isMC=False):
    selection = []
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    if isMC:
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    for channel, value in enumerate(charge_channels_to_use):
        if value:
            part = "(channel==%i)" % channel
            selection.append(part)
    selection = "||".join(selection)
    return "(%s)" % selection

def get_noise_cut(energy_threshold=35.0,isMC=False):
    selection = []
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    if isMC:
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    for channel, value in enumerate(charge_channels_to_use):
        if value:
            part = "((baseline_rms[%i]*calibration[%i]>%s)||(energy_rms1[%i]>%s))" % (
                channel, 
                channel, 
                energy_threshold,
                channel, 
                energy_threshold,
            )
            selection.append(part)
    selection = "+".join(selection)
    return "(%s==0)" % selection

def pmt_chisq_per_dof(pmt_hist, wfm_hist, electronics_noise=0.0):
    """
    This is used to calculate chi^2/dof compared to PMT hist, in generateTier3.py
    """
    chisq_per_dof = 0.0
    for i in xrange(pmt_hist.GetNbinsX()):
        i_bin = i+1
        val = pmt_hist.GetBinContent(i_bin) - wfm_hist.GetBinContent(i_bin)
        error = math.sqrt(
            math.pow(pmt_hist.GetBinError(i_bin), 2.0) + \
            math.pow(electronics_noise, 2.0)
        ) 
        if error > 0.0:
            chisq_per_dof += val*val/(error*error)
    return chisq_per_dof/i




if __name__ == "__main__":

    print "\nnegative energy cut:"
    print "\t" + "\n\t ||".join(get_negative_energy_cut().split("||"))

    print "\ndrift time cut:"
    print "\t" + "\n\t ||".join(get_drift_time_cut().split("||"))

    print "\ndrift time selection:"
    print "\t" + "\n\t ||".join(get_drift_time_selection().split("||"))

    print "\ndrift time selection:"
    print "\t" + "\n\t ||".join(get_drift_time_selection(drift_time_high=struck_analysis_parameters.max_drift_time).split("||"))

    print "\nget_few_channels_cmd:"
    print "\t" + "\n\t +".join(get_few_channels_cmd().split("+"))

    print "\nget_chargeEnergy_no_pz:"
    print "\t", get_chargeEnergy_no_pz()

    print "\nget_energy_weighted_drift_time:"
    print "\t" + "\n\t +".join(get_energy_weighted_drift_time().split("+"))

    print "\n get_multiplicity_cmd:"
    print get_multiplicity_cmd()

    print "\n get_single_strip_cut:"
    print get_single_strip_cut()

    print "\n get_corrected_energy_cmd:"
    print get_corrected_energy_cmd()

    print "\n get_fiducial_cut:"
    print get_fiducial_cut(energy_threshold=10)

    print "\n get_channel_selection:"
    print get_channel_selection()

    print "\n get_channel_selection (MC):"
    print get_channel_selection(isMC=True)

    print "\n get_noise_cut:"
    print get_noise_cut()

    #print "\n"+ get_drift_time_cut(energy_threshold=200,drift_time_low=7.0,drift_time_high=8.5)
    #print "\n"+ get_drift_time_cut(drift_time_low=7.0,drift_time_high=8.0)
    print "\n get_drift_time_cut(): \n"+ get_drift_time_cut()
    print "\n get_drift_time_cut(drift_time_high=9.0): \n"+ get_drift_time_cut(drift_time_high=9.0)
    print "\n get_drift_time_cut(drift_time_high=9.0, isMC=True): \n"+ get_drift_time_cut(drift_time_high=9.0,isMC=True)
    print "\n get_drift_time_cut(drift_time_high=9.0, is_single_channel=True): \n"+ get_drift_time_cut(drift_time_high=9.0,is_single_channel=True)
    print "\n get_drift_time_selection(drift_time_high=9.0, is_single_channel=True): \n" + get_drift_time_selection(drift_time_high=9.0,is_single_channel=True)
    print "\n"+ get_single_strip_cut(isMC=True)

    #print "\n" + get_negative_energy_cut()
    #print "\n"+ get_drift_time_cut(drift_time_low=7.0,drift_time_high=8.0,isMC=True)
    #print "\n"+ get_drift_time_cut(drift_time_low=8.0,drift_time_high=9.0,isMC=True)

    #print "\n"+ get_drift_time_cut(drift_time_low=8.0,drift_time_high=10.0)

    print "\n get_few_channels_cmd: \n" + get_few_channels_cmd()

    print "\n get_drift_time_cut:", get_drift_time_cut(is_single_channel=True)


