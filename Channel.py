"""
This script contains a channel object for the reach averaged forest resistance model.
The class is used in the Hydraulics.py script.
"""
from scipy import optimize
from Forest import Forest
from Forest import CasOver
import pandas as pd
import os
from Logger import LogFile
import math

# Global variables
water_density = 998.0  # kg/m3
g = 9.81  # m2/s - gravitational acceleration
kappa = 0.41  # von Karman constant

'''
Simple rectangular channel class for simple hydraulic modelling. The channel
is assigned a forest. Then, forest averaged resistance is simulated.
'''


class RectChannel:
    def __init__(self, width=0, length=0, slope=0.0):
        self.width = width
        self.length = length
        self.bed_slope = slope
        self.n = 0.03
        self.sidewalls = False
        self.water_depth = 0.0
        self.forest_depth = 0.0
        self.submergence_depth = 0.0
        self.water_level = 0.0
        self.friction_slope = 0.0
        self.drag_slope = 0.0
        self.energy_slope = slope
        self.flow_velocity = 0.0
        self.forest_velocity = 0.0
        self.submergence_velocity = 0.0
        self.rigid_velocity = 0.0
        self.reconfiguration_velocity = 0.0
        self.plan_area = width * length
        self.forest = Forest(self.plan_area)
        self.initial_u = 0.5
        self.all_slopes = []
        self.hydraulics_df_file = pd.DataFrame()
        self.flow_depths = []
        self.flow_levels = []
        self.home_path = ''
        self.logger = LogFile()
        self.use_flow_depths = False
        self.use_flow_levels = False
        self.use_absolute_depths = False
        self.use_tree_database = False
        self.submergence = 'emergent'
        self.is_ruptured = False
        self.blockage = True
        self.result_suffix_decimals = 0

    def read_ufm_file(self, ufm):
        self.logger.set_log_file_name(ufm)
        self.forest.assign_ufm(ufm)
        self.home_path = os.path.dirname(ufm)
        # Current date time in local system
        try:
            f = open(ufm, 'r')  # 'r' = read
            lines = f.readlines()
            lines = self.strip_comments(lines)
            self.read_ufm_lines(lines)
        except IOError:
            self.logger.log('the file could not be accessed: {}'.format(ufm))
        finally:
            f.close()

    def read_ufm_lines(self, lines):
        for line in lines:
            # print(line)
            if 'Channel Width =='.upper() in line.upper():
                str_parse = line.split('==')
                self.width = float(str_parse[1].strip())
                self.logger.log('Channel width: {} m'.format(self.width))
            if 'Channel Length =='.upper() in line.upper():
                str_parse = line.split('==')
                self.length = float(str_parse[1].strip())
                self.logger.log('Channel length: {} m'.format(self.length))
            if 'Channel Slopes (km) =='.upper() in line.upper():
                str_parse = line.split('==')
                slope_file = '{}\\{}'.format(self.home_path, str_parse[1].strip())
                self.logger.log('Channel slope file: {}'.format(slope_file))
            if 'Channel Sidewalls =='.upper() in line.upper():
                str_parse = line.split('==')
                if str_parse[1].strip().upper() == "TRUE":
                    self.sidewalls = True
                self.logger.log('Use channel sidewalls: {}'.format(str(self.sidewalls)))
            if 'Trees Ruptured == True'.upper() in line.upper():
                self.is_ruptured = True
                self.logger.log('The forest is ruptured!')
            if 'Channel Mannings n =='.upper() in line.upper():
                str_parse = line.split('==')
                self.n = float(str_parse[1].strip())
                self.logger.log('Channel bed roughness (Mannings n): {}'.format(self.n))
            if 'Tree Type =='.upper() in line.upper():
                str_parse = line.split('==')
                tree_type = str_parse[1].strip()
                self.logger.log('Tree type: {}'.format(tree_type))
            if 'Tree Height =='.upper() in line.upper():
                str_parse = line.split('==')
                tree_height = float(str_parse[1].strip())
                self.logger.log('Tree height: {} m'.format(tree_height))
            if 'Tree Width =='.upper() in line.upper():
                str_parse = line.split('==')
                tree_width = float(str_parse[1].strip())
                self.logger.log('Tree height: {} m'.format(tree_width))
            if 'Tree Population =='.upper() in line.upper():
                str_parse = line.split('==')
                tree_population = int(str_parse[1].strip())
                self.logger.log('Number of trees: {}'.format(tree_population))
            if 'Set depths == absolute'.upper() in line.upper():
                self.use_absolute_depths = True
            if 'Flow depths =='.upper() in line.upper():
                self.use_flow_depths = True
                str_parse = line.split('==')
                flow_depth_file = '{}\\{}'.format(self.home_path, str_parse[1].strip())
                self.logger.log('Flow depths file: {}'.format(flow_depth_file))
            if 'Flow levels =='.upper() in line.upper():
                self.use_flow_levels = True
                str_parse = line.split('==')
                flow_level_file = '{}\\{}'.format(self.home_path, str_parse[1].strip())
                self.logger.log('Flow levels file: {}'.format(flow_level_file))
            if 'Tree DB =='.upper() in line.upper():
                self.use_tree_database = True
                str_parse = line.split('==')
                tree_db_file = '{}\\{}'.format(self.home_path, str_parse[1].strip())
                self.logger.log('Tree database file: {}'.format(tree_db_file))
            if 'Blockage == None'.upper() in line.upper():
                self.blockage = False
                self.logger.log('Not using blockage factors')
            if 'Result file suffix decimals =='.upper() in line.upper():
                str_parse = line.split('==')
                self.result_suffix_decimals = int(str_parse[1].strip())
                self.logger.log('Number of decimals to use in the suffix of the results file: {}'
                                .format(self.result_suffix_decimals))

        # set up the forest
        self.plan_area = self.width * self.length
        self.forest.plan_area = self.plan_area
        if self.use_tree_database:
            self.forest.read_database(tree_db_file)
        else:
            if tree_type == 'Casuarina-overstory':
                self.forest.add_tree(CasOver(height=tree_height,
                                             number_of_specimens=tree_population,
                                             canopy_width=tree_width))

        # get the slopes
        self.logger.log(' ')
        self.logger.log('opening slope file...')
        self.logger.log(os.path.abspath(slope_file))
        df = pd.read_csv(slope_file)
        self.all_slopes = df['Slopes'].values

        # get the flow depths
        if self.use_flow_depths:
            self.logger.log(' ')
            self.logger.log('opening hydraulics template file...')
            self.logger.log(os.path.abspath(flow_depth_file))
            self.hydraulics_df_file = flow_depth_file
            df = pd.read_csv(flow_depth_file, index_col=0)
            if self.use_absolute_depths:
                self.flow_depths = df['Flow_Depth'].values
            else:
                self.flow_depths = df['Flow_Depth'].values * tree_height

        # get the flow levels
        if self.use_flow_levels:
            self.logger.log(' ')
            self.logger.log('opening hydraulics template file...')
            self.logger.log(os.path.abspath(flow_depth_file))
            self.hydraulics_df_file = flow_level_file
            df = pd.read_csv(flow_level_file, index_col=0)
            self.flow_levels = df['Flow_Level'].values

        # print some info
        self.set_water_depth(1)
        self.forest.output_geometry()

    def strip_comments(self, lines):
        sep = '!'
        stripped_lines = []
        for line in lines:
            i = line.find(sep)
            if i >= 0:
                line = line[:i]
            line = line.strip()
            if line: stripped_lines.append(line)
        return stripped_lines

    def set_bed_slope(self, slope):
        self.bed_slope = slope
        self.energy_slope = slope

    def set_mannings_n(self, n):
        self.n = n

    def set_sidewalls(self, choice):
        self.sidewalls = choice

    def set_water_depth(self, h):
        if not self.use_flow_depths and self.use_flow_levels:
            self.set_water_level(h)
        else:
            self.water_depth = h
            self.forest.set_flow_depth(h)

    def set_water_level(self, h):
        self.water_level = h
        self.forest.set_flow_level(h)

    def channel_volume(self):
        return self.plan_area * self.water_depth

    def flow_area(self, depth=-1.0):
        if depth < 0:
            depth = self.water_depth
        return self.width * depth

    def wet_perimeter(self):
        return self.width + 2 * self.water_depth

    def hydraulic_radius(self):
        # this is for the forest layer only
        hyd_radius = self.forest_depth * (1.0 - self.cell_width_factor())
        if self.submergence == 'submerged':
            hyd_radius = hyd_radius + self.submergence_depth
        return hyd_radius

    def bed_shear_stress(self, u):
        # this is for the forest layer only
        return (water_density * g * self.n**2.0 * self.theta()
                / self.forest_depth ** (1.0 / 3.0)
                * u**2.0)

    def total_shear_stress(self):
        R = self.forest_depth * (1.0 - self.storage_reduction_factor())
        if self.submergence == 'submerged':
            R = R + self.submergence_depth
        return water_density * g * R * self.energy_slope

    def rupture_forest(self):
        for tree in self.forest.trees:
            tree.rupture_tree()

    def resolve_velocity(self):

        #  check if ruptured
        if self.is_ruptured:
            self.rupture_forest()
            print('Forest is ruptured...')

        #  get the forest canopy height
        self.forest_depth = self.forest.canopy_height(self.is_ruptured)

        #  set emergence state
        self.submergence = 'emergent'
        self.submergence_depth = self.water_depth - self.forest_depth
        if self.submergence_depth > 0.001:
            self.submergence = 'submerged'
            self.forest.set_flow_depth(999.0)  # set flow depth to tree height

        print('Water depth: {0:0.2f}    Canopy height: {1:0.2f}    State: {2}'.
              format(self.water_depth, self.forest_depth, self.submergence))

        if self.submergence == 'emergent':
            self.forest_depth = self.water_depth

        # Get the rigid velocity and check if there is reconfiguration
        R = self.forest_depth*(1-self.cell_width_factor())
        rigid_u = 1/self.rigid_composite_n() * R**(2.0/3.0) * math.sqrt(self.energy_slope)
        print('Rigid_velocity: {0:0.3f}m/s Mannings n: {1:0.3f}  theta_a: {2:0.2f}'
              .format(rigid_u, self.rigid_composite_n(), self.cell_width_factor()))
        if self.forest.check_if_rigid(rigid_u):
            self.forest_velocity = rigid_u
        # Get the reconfiguration velocity if needed
        else:
            opt_result = optimize.newton(
                lambda u: (self.bed_shear_stress(u)
                           + self.forest.drag_shear(u)
                           - self.total_shear_stress()), 1)
            self.forest_velocity = opt_result

        # Print some metrics to the console for checking
        tree = self.forest.trees[0]
        print('bed stress: {0:0.2f} forest stress: {1:0.2f} total stress: {2:0.3f} drag: {3:0.3f} area: {4:0.3f}'
              .format(self.bed_shear_stress(self.forest_velocity),
                      self.forest.drag_shear(self.forest_velocity),
                      self.total_shear_stress(),
                      tree.drag_force(self.forest_velocity),
                      tree.area_h()))

        # Submergence layer
        if self.submergence_depth > 0.001:
            #print('The canopy is submerged by a depth of {0:.3f} m'.format(self.submergence_depth))
            self.submergence = 'submerged'
            self.submergence_velocity = self.submergence_layer_velocity(self.forest_velocity)
            self.flow_velocity = ((self.forest_depth * self.forest_velocity * (1 - self.cell_width_factor())
                                  + self.submergence_depth * self.submergence_velocity) /
                                  self.water_depth)
        else:
            self.flow_velocity = self.forest_velocity
        # print('velocity found: {0:.3f}'.format(self.flow_velocity))

    def submergence_layer_velocity(self, uf):
        shear_u = math.sqrt(g * self.submergence_depth * self.energy_slope)
        K = self.forest.Cu * shear_u / kappa
        us = self.water_depth / self.submergence_depth * math.log(self.water_depth / self.forest_depth) - 1
        return K * us + uf

    def conversion_error(self):
        # return int(round((self.friction_slope+self.drag_slope-self.energy_slope)/self.energy_slope*100))
        return int(round((self.bed_shear_stress(self.forest_velocity)
                          + self.forest.drag_shear(self.forest_velocity)
                          - self.total_shear_stress())
                         / self.total_shear_stress() * 100))

    def get_mannings_n(self):
        return self.hydraulic_radius()**(2/3)*self.energy_slope**(1/2)/self.flow_velocity

    def get_q_unblocked(self):
        return self.flow_area()*self.flow_velocity/self.width

    def effective_flow_area(self):
        return (self.channel_volume() - self.forest.volume())/self.length

    def get_q_blocked(self):
        return self.effective_flow_area()*self.flow_velocity/self.width

    def threshold_velocity(self):
        return self.forest.u0

    def mannings_u(self):
        return 1/self.n*self.water_depth**(2.0/3.0)*self.energy_slope**0.5

    def cell_width_factor(self):
        if self.blockage:
            cwf = math.sqrt(self.storage_reduction_factor())
        else:
            cwf = 0.0

        return cwf

    def storage_reduction_factor(self):
        if self.blockage:
            srf = self.forest.total_plan_area()/self.plan_area
        else:
            srf = 0.0
        if srf > 0.9:
            srf = 0.9
            print('!!!WARNING: Storage reduction factor is large!')
        return srf

    def theta(self):
        exp = 4.0/3.0
        numerator = 1.0 - self.storage_reduction_factor()
        denominator = (1.0 - self.cell_width_factor())**exp
        return numerator / denominator

    def rigid_forest_n(self):
        numerator = self.forest_depth**(1.0/3.0) * self.forest.total_rigid_speed_specific_drag()
        denominator = water_density * g * self.plan_area * self.theta()
        return math.sqrt(numerator/denominator)

    def rigid_composite_n(self):
        return math.sqrt(self.n**2 + self.rigid_forest_n()**2)
