
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


def get_negative_energy_cut(threshold=-20.0):
    """
    return a cut on events with too much negative energy on any one channel
    """

    selection = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
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
    selection = "!(%s)" % selection

    return selection


def get_short_drift_time_cut(
    energy_threshold=200.0,
    drift_time_cut=struck_analysis_parameters.drift_time_threshold,
):
    """
    Cut any events with energy above threshold and too short a drift time
    """

    selection = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            cut = "((energy1_pz[%i]>%s) && (rise_time_stop95[%i]-trigger_time<%s))" % (
                channel,
                energy_threshold,
                channel,
                drift_time_cut,
            )
            #print cut
            selection.append(cut)

    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses and add not
    selection = "!(%s)" % selection

    return selection



def get_long_drift_time_cut(
    energy_threshold=200.0,
    drift_time_low=struck_analysis_parameters.drift_time_threshold,
    drift_time_high=None,
):
    """
    Select events with energy above threshold and long enough drift time
    """

    selection = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
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
                part = "(rise_time_stop95[%i]-trigger_time<%s)" % (
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
                part = "(rise_time_stop95[%i]-trigger_time>%s)" % (
                    channel,
                    drift_time_high,
                )
                cut2.append(part)
                cut.append("&&".join(cut2))
            #print cut
            cut = "||".join(cut)
            selection.append(cut)
            
    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses
    selection = "!(%s)" % selection

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

def get_multiplicity_cmd(energy_threshold=100.0):
    """A draw command for multiplicity """
    draw_cmd = []
    for channel, value in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            draw_cmd.append("(energy1_pz[%i]>%s)" % (channel,energy_threshold))
    # join each part with "+"
    draw_cmd = "+".join(draw_cmd)
    return draw_cmd

def get_single_strip_cut(energy_threhold=10.0):
    """Select events with only one channel above threshold"""
    selection = "(%s==1)" % get_multiplicity_cmd(energy_threhold)
    return selection

def get_few_channels_cmd(
    energy_threshold=100.0,
):
    """ A draw command for total energy, only including  events above threshold """
    draw_cmd = []
    for channel, value  in enumerate(struck_analysis_parameters.charge_channels_to_use): 
        if value:
            part = "(energy1_pz[%i]>%s)*energy1_pz[%i]" % (
                channel, 
                energy_threshold,
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
    if get_short_drift_time_cut() in selection:
        label.append("SC")
    if get_long_drift_time_cut() in selection:
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


if __name__ == "__main__":

    print "\nnegative energy cut:"
    print "\t" + "\n\t ||".join(get_negative_energy_cut().split("||"))

    print "\nshort drift time cut:"
    print "\t" + "\n\t ||".join(get_short_drift_time_cut().split("||"))

    print "\nlong drift time cut:"
    print "\t" + "\n\t ||".join(get_long_drift_time_cut().split("||"))

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
    print get_fiducial_cut()

    #print "\n"+ get_long_drift_time_cut(energy_threshold=200,drift_time_low=7.0,drift_time_high=8.5)
    print "\n"+ get_long_drift_time_cut(drift_time_high=8.5)

