"""
The classes include Forest(), which is a container of the Tree() class. Forest() is passed
to the Channel.py file to be included in a channel object.
"""
import math
from Logger import LogFile
import pandas as pd
import numpy as np

# GLOBAL VARIABLES
water_density = 998  # kg/m3
delta_U0_threshold = 0.001  # m/s -- used to stop bouncing around U0

'''
This class is a container for individual trees (Tree() class), and is passed to the channel 
class. The total drag stress is computed. The forest is set up using a uniform flow model
(ufm) file, which is passed to the python script using a batch file.
'''


class Forest:
    def __init__(self, plan_area=1.0):
        self.plan_area = plan_area
        self.trees = []
        self.flow_depth = 0.0
        self.flow_level = 0.0
        self.u0 = 0.0
        self.logger = LogFile()
        self.Cu = 1 # Yang and Choi (2010) = 1 if a < 5 m-1

    def read_database(self, filename):
        df = pd.read_csv(filename)
        self.logger.log('Reading tree database...')
        # print(df)

        for index, row in df.iterrows():
            if row.Type == 'Casuarina-overstory':
                # self.logger.log(row)
                self.add_tree(CasOver(row.Height, row.Population, row.GroundLevel))
            else:
                self.logger.log('Error: !!! tree type not recognised !!!')
    def assign_ufm(self, ufm):
        self.logger.set_log_file_name(ufm)

    def average_tree_height(self):
        cumulator = 0
        counter = 0
        for tree in self.trees:
            if tree.height > 0.001:
                counter += tree.number_of_specimens
                cumulator += tree.height * tree.number_of_specimens
        return cumulator / counter

    def average_canopy_width(self):
        cumulator = 0
        counter = 0
        for tree in self.trees:
            if tree.canopy_width > 0.001:
                counter += tree.number_of_specimens
                cumulator += tree.canopy_width * tree.number_of_specimens
        return cumulator / counter

    def canopy_height(self, is_ruptured):
        if is_ruptured:
            return self.average_canopy_width() / 2
        else:
            return self.average_tree_height()

    def add_tree(self, new_tree):
        self.trees.append(new_tree)

    def get_tree(self, ind):
        return self.trees[ind]

    def population(self):
        population = 0
        for tree in self.trees:
            population += tree.number_of_specimens
        return population

    def density(self):
        return self.population() / self.plan_area

    def set_flow_depth(self, h):
        self.flow_depth = h
        for tree in self.trees:
            if tree.height > h:
                tree.flow_depth = h
            else:
                tree.flow_depth = tree.height

    def set_flow_level(self, h):
        self.flow_level = h
        for tree in self.trees:
            tree.flow_depth = h - tree.ground_level
            if tree.flow_depth > tree.height:
                tree.flow_depth = tree.height
            elif tree.flow_depth < 0.001:
                tree.flow_depth = 0.0001

    def total_drag(self, u):
        cumulative_drag = 0.0
        for tree in self.trees:
            if tree.flow_depth > 0.001:  # using depth of 0.001m as a threshold for computing drag
                cumulative_drag += tree.drag_force(u) * tree.number_of_specimens
        return cumulative_drag

    def total_rigid_speed_specific_drag(self):
        cumulative_drag = 0.0
        for tree in self.trees:
            if tree.flow_depth > 0.001:  # using depth of 0.001m as a threshold for computing drag
                cumulative_drag += tree.rigid_speed_specific_drag() * tree.number_of_specimens
        return cumulative_drag

    def check_if_rigid(self, u):
        rigid = True
        for tree in self.trees:
            # print('Transition u: {}'.format(tree.threshold_velocity()))
            if (u / tree.threshold_velocity()) > 0.001:
                rigid = False
        return rigid

    def drag_shear(self, u):
        return self.total_drag(u) / self.plan_area

    def get_average_threshold_velocity(self):
        tree = self.trees[0]
        tree.height = self.average_tree_height()
        return tree.threshold_velocity()

    def get_reconfiguration_regime_proportion(self):
        hit_counter = 0
        total_counter = 0
        for tree in self.trees:
            total_counter += 1
            if tree.drag_regime == 'reconfiguration':
                hit_counter += 1
        return round(hit_counter / total_counter * 100)

    def volume(self):
        cumulative_volume = 0.0
        for tree in self.trees:
            ave_diameter = tree.area_h()/tree.flow_depth
            cumulative_volume += math.pi*ave_diameter**2/4 * tree.flow_depth
        return cumulative_volume

    def total_frontal_area(self):
        cumulative_area = 0.0
        for tree in self.trees:
            cumulative_area += tree.area_h() * tree.number_of_specimens
        return cumulative_area

    def total_plan_area(self):
        cumulative_area = 0.0
        for tree in self.trees:
            ave_diameter = tree.area_h() / tree.flow_depth
            cumulative_area += math.pi * ave_diameter ** 2 / 4 * tree.number_of_specimens
        return cumulative_area

    def output_geometry(self):
        self.logger.log(' ')
        self.logger.log('Number of trees is: {}'.format(self.population()))
        self.logger.log('Forest area is: {} m²'.format(self.plan_area))
        self.logger.log('Forest tree density is: {0:.3f} trees per m²'.format(self.density()))
        self.logger.log('The total tree volume at depth 1 m is: {0:.2f} m3'.format(self.volume()))
        self.logger.log('The shear stress from tree drag for a velocity of 1 m/s is: {0:.2f} Pa'.format(
            self.drag_shear(1)))
        self.logger.log(' ')
        return ''


'''
This class is a template (parent) for the tree types/species it is for an individual 
tree, which is passed to the Forest() class. Drag and allometric parameters are set in 
child classes.
'''


class Tree:
    def __init__(self, height, number_of_specimens=1, ground_level=0.0, canopy_width=0, tree_id=''):
        self.species = ''
        self.height = height
        self.area_parameters = [0, 0]
        self.area_h_parameters = [0, 0, 0, 0]
        self.first_area_parameters = [0, 0]
        self.first_area_h_parameters = [0, 0, 0, 0, 0, 0]
        self.diameter_parameters = [0, 0]
        self.diameter_h_parameters = [0, 0]
        self.modulus_parameters = [0, 0]
        self.drag_parameters = [0, 0, 0]
        self.flow_depth = 0.0
        self.drag_regime = ''
        self.ground_level = ground_level
        self.number_of_specimens = number_of_specimens
        self.water_level = 0.0
        self.canopy_width = canopy_width
        self.tree_id = tree_id

    def power_func(self, a, b):
        return a * self.height ** b

    def sig_func(self, i, j, k, l, m, h=-1.0):
        if h < 0: h = self.flow_depth
        return -i/(j*(k + (h/self.height)**m)) + l

    def quad_func(self, a, b, h=-1.0):
        if h < -0.5: h = self.flow_depth
        result = (1-(a*(h/self.height)**2+b*(h/self.height)))*self.base_diameter()
        if result < 0:
            return 0
        else:
            return result

    def area(self):
        return self.power_func(*self.area_parameters)

    def area_h(self, h=-1.0):
        # area = self.sig_func(*self.area_h_parameters, h) * self.area()
        if h < 0: h = self.flow_depth
        coef = self.area_h_parameters
        x = h/self.height
        # a = coef[0]*x**4 + coef[1]*x**3 + coef[2]*x**2 + coef[3]*x
        i, j, k, l, m = coef
        a = -i / (j * (k + x ** m)) + l
        if a > 1.0:
            a = 1.0
        area = a * self.area()
        if area > 0.001:
            return area
        else:
            return 0.0001

    def first_area(self):
        return self.power_func(*self.first_area_parameters)

    def first_area_h(self, h=-1.0):
        if h < 0: h = self.flow_depth
        # return self.sig_func(*self.first_area_h_parameters)*self.first_area()
        a = self.area_h()/self.area()
        z = self.first_area_h_parameters[0] * a**2 + self.first_area_h_parameters[1] * a
        # coef = self.first_area_h_parameters
        # x = h / self.height
        # z = coef[0] * x ** 4 + coef[1] * x ** 3 + coef[2] * x ** 2 + coef[3] * x

        Z_h = z * self.first_area()
        if 0.001 < self.flow_depth < 0.01:
            print('Shallow depth... modifying first moment of area')
            Z_h = self.area_h() * self.flow_depth/2

        if Z_h > 0.001:
            return Z_h
        else:
            return 0.0001

    def base_diameter(self):
        return self.power_func(*self.diameter_parameters)

    def base_diameter_h(self, h=-1.0):
        return self.quad_func(*self.diameter_h_parameters, h)

    def threshold_velocity(self):
        modulus = self.power_func(*self.modulus_parameters)
        Cd = self.drag_parameters[0]
        if self.flow_depth > 0.001:
            threshold_u = math.sqrt(2*modulus/(water_density*Cd*self.first_area_h()*self.flow_depth))
        else:
            threshold_u = 99999
        return threshold_u

    def set_water_level(self, water_level):
        self.water_level = water_level
        self.flow_depth = water_level - self.ground_level
        # print('WL: {}    GL: {}   D: {}'.format(water_level, self.ground_level, self.flow_depth))
        if self.flow_depth > self.height:
            self.flow_depth = self.height
        elif self.flow_depth < 0.001:
            self.flow_depth = 0.0001

    def rigid_speed_specific_drag(self):
        if self.flow_depth > 0.001:
            Cd, vogel_exp = self.drag_parameters
            return 0.5*water_density*Cd*self.area_h()
        else:
            return 0.0

    def drag_force(self, u):
        if self.flow_depth > 0.001:
            Cd, vogel_exp = self.drag_parameters
            reconfiguration_term = u / self.threshold_velocity()
            if reconfiguration_term < 1:
                reconfiguration_term = 1
                self.drag_regime = 'rigid'
            else:
                self.drag_regime = 'reconfiguration'
            reconfiguration_term = reconfiguration_term**vogel_exp
            return 0.5*water_density*Cd*self.area_h()*u**2.0*reconfiguration_term
        else:
            return 0.0

    def bent_height(self, u):
        col_headers = np.array(['s', 'Area', 'dA', 'dQ', 'Q', 'Trunk_dia', 'I', 'EI', 'Fd', 'Md', 'R'])
        slices = 1000
        s_values = np.linspace(0.0, self.flow_depth, slices)
        data = np.zeros([s_values.shape[0], col_headers.shape[0]], dtype=float)
        data[:, 0] = s_values
        delta_s = s_values.item(1)

        df = pd.DataFrame(data, columns=col_headers)
        bulk_modulus = self.power_func(*self.modulus_parameters)
        base_dia = self.base_diameter()
        modulus = bulk_modulus/(math.pi*(base_dia/2)**4/4)  # check the B units aren't MPa??
        drag_force = self.drag_force(u)
        area = self.area_h()
        q = self.first_area_h()

        # get the area and delta Q
        df['Area'] = self.area_h(df['s'])
        df.loc[0, 'dA'] = df.loc[0, 'Area']
        df.loc[1:, 'dA'] = df.loc[2:, 'Area'] - df.loc[1:-2, 'Area']
        df['dQ'] = df['dA']*df['s']+delta_s/2
        df['Q'] = df.loc[::-1, 'dQ'].cumsum()[::-1]
        df['Trunk_dia'] = self.base_diameter_h(df['s'])
        df['I'] = math.pi*(df['Trunk_dia']/2)**4/4
        df['EI'] = df['I'] * modulus
        df['Fd'] = df['dA'] / area * drag_force
        df['Md'] = df['Fd'] * q/area
        df['R'] = df['EI'] / df['Md']

    def output_geometry(self):
        self.logger.log(' ')
        self.logger.log('Output geometry for {} tree at full height ({} m):'.format(self.species, self.height))
        self.logger.log('Projected area is: {0:.2f} m²'.format(self.area()))
        self.logger.log('First moment of area is: {0:.2f} m³'.format(self.first_area()))
        self.logger.log('Trunk base diameter is: {0:.3f} m'.format(self.base_diameter()))
        self.logger.log(' ')
        self.logger.log('Output geometry for {} tree at partial height ({} m):'.format(self.species, self.flow_depth))
        self.logger.log('Projected area is: {0:.2f} m²'.format(self.area_h()))
        self.logger.log('First moment of area is: {0:.2f} m³'.format(self.first_area_h()))
        self.logger.log('Trunk base diameter is: {0:.3f} m'.format(self.base_diameter_h()))
        self.logger.log('Threshold velocity is: {0:.3f} m/s'.format(self.threshold_velocity()))
        self.logger.log('Tree drag for a velocity of 1 m/s is: {0:.1f} N'.format(self.drag_force(1)))
        return ''

    def __repr__(self):
        return 'Tree: {}'.format(self.tree_id)

    def __str__(self):
        return 'Tree: {}'.format(self.tree_id)


'''
This class is a child of the Tree() class and contains the parameters for 
Casuarina overstorey trees.
'''


class CasOver(Tree):
    def __init__(self, height, number_of_specimens=1, ground_level=0.0, canopy_width=0, tree_id=''):
        Tree.__init__(self, height, number_of_specimens, ground_level, canopy_width, tree_id)
        self.species = 'CasOver'
        self.area_parameters = [0.5982, 1.331]
        # self.area_h_parameters = [1.217, - 4.062, 3.518, 0.3299]
        self.area_h_parameters = [1.274, 5.0, 0.2104, 1.210, 2.137]
        self.first_area_parameters = [0.2557, 2.3311]
        # self.first_area_h_parameters = [-1.892, 1.385, 1.598, -0.1013]
        self.first_area_h_parameters = [0.8881, 0.1119]
        self.diameter_parameters = [0.01, 1.15]
        self.diameter_h_parameters = [-0.246, 1.19]
        self.modulus_parameters = [2.437, 3.667]
        self.drag_parameters = [0.1198, -0.8801]  # Cd0 and Vog exp from CY model

    def rupture_tree(self):
        self.drag_parameters = [0.084, -0.587]  # Cd0 and Vog exp from CY model
