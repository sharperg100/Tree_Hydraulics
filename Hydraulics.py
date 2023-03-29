"""
This script runs the reach averaged forest resistance model. The model is run from
a batch file, and parameterised through a plain text file (*.ufm).
"""
from Channel import RectChannel
import pandas as pd
from Logger import LogFile
import os
import sys
from math import modf


def main():
    ufm_file = os.path.join(os.path.abspath(str(sys.argv[2])), sys.argv[1])
    # ufm_file = 'C:/Python_projects/Tree_Hydraulics/model/Dayboro_WTP/Dayboro_WTP_2009_0p6.ufm'

    # Set up the channel
    model_logger = LogFile()
    model_logger.initialise(ufm_file)
    model_logger.log_event_start()
    my_channel = RectChannel()
    my_channel.read_ufm_file(ufm_file)
    my_channel.logger = model_logger
    if my_channel.use_flow_depths:
        hydraulics_depths(my_channel, model_logger)


def hydraulics_depths(my_channel, model_logger):
    # hydraulic metrics containers
    df = pd.read_csv(my_channel.hydraulics_df_file, index_col=0)
    velocities = []
    uf = []
    us = []
    mannings = []
    q_blocked = []
    q_unblocked = []
    slopes = []
    drag_regime = []
    conversion_errors = []
    u0 = []
    bare_u_values = []
    cwf = []
    srf = []
    af = []

    # solve hydraulics
    for channel_slope in my_channel.all_slopes:
        model_logger.log('resolving velocity for slope: 1 m in / {} km'.format(channel_slope))
        my_channel.set_bed_slope(1/(channel_slope*1000))
        for flow_depth in my_channel.flow_depths:
            my_channel.set_water_depth(flow_depth)
            my_channel.resolve_velocity()
            velocities.append(my_channel.flow_velocity)
            bare_u_values.append(my_channel.mannings_u())
            mannings.append(my_channel.get_mannings_n())
            slopes.append(my_channel.energy_slope)
            q_unblocked.append(my_channel.get_q_unblocked())
            q_blocked.append(my_channel.get_q_blocked())
            drag_regime.append(my_channel.forest.get_reconfiguration_regime_proportion())
            conversion_errors.append(my_channel.conversion_error())
            u0.append(my_channel.forest.get_average_threshold_velocity())
            uf.append(my_channel.forest_velocity)
            us.append(my_channel.submergence_velocity)
            cwf.append(my_channel.cell_width_factor())
            srf.append(my_channel.storage_reduction_factor())
            af.append(my_channel.forest.total_frontal_area())

            model_logger.log('h: {0:>4.2f}    U: {1:>6.3f}    recon regime: {2:>3}%    Error: {3:>3} %    {4}'
                             .format(flow_depth,
                                     my_channel.flow_velocity,
                                     my_channel.forest.get_reconfiguration_regime_proportion(),
                                     my_channel.conversion_error(),
                                     my_channel.submergence))

        # store results
        df.Flow_Depth = my_channel.flow_depths
        df.Velocity = velocities
        df.Bare_U = bare_u_values
        df.Mannings_n = mannings
        df.Slope = slopes
        df.Q_unblocked = q_unblocked
        df.Q_blocked = q_blocked
        df.Regime = drag_regime
        df.Error = conversion_errors
        df.U0 = u0
        df.forest_u = uf
        df.submergence_u = us
        df.CWF = cwf
        df.SRF = srf
        df.Tot_Af = af

        model_logger.log('writing results for slope: 1 m in / {} m'.format(str(round(1000*channel_slope))))

        if my_channel.result_suffix_decimals > 0:
            split_slope = modf(1000 * channel_slope)
            left_slope = int(split_slope[1])
            right_slope = int(split_slope[0] * 10**my_channel.result_suffix_decimals)
            result_suffix = '_{}pt{}'.format(left_slope, right_slope)
        else:
            result_suffix = '_pt{}'.format(int(1000*channel_slope))

        result_file_name = '{}/results/hydraulics_results{}.csv'.format(my_channel.home_path, result_suffix)
        model_logger.log('Filename...')
        model_logger.log(os.path.abspath(result_file_name))
        df.to_csv(result_file_name)


        # clear the lists
        velocities.clear()
        us.clear()
        uf.clear()
        mannings.clear()
        q_blocked.clear()
        q_unblocked.clear()
        slopes.clear()
        drag_regime.clear()
        conversion_errors.clear()
        u0.clear()
        bare_u_values.clear()
        cwf.clear()
        srf.clear()
        af.clear()

        model_logger.log('Done...')
        model_logger.log(' ')

    model_logger.log_event_end()


if __name__ == "__main__":
    main()
