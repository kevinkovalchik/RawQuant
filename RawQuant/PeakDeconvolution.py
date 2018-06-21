import numpy as np
import pandas as pd


class IsotopeProfile:

    coeff = dict()
    coeff['0S'] = {'R1': (-0.00142320578040, 0.53158267080224, 0.00572776591574, -0.00040226083326, -0.00007968737684),
                   'R2': (0.06258138406507, 0.24252967352808, 0.01729736525102, -0.00427641490976, 0.00038011211412),
                   'R3': (0.03092092306220, 0.22353930450345, -0.02630395501009, 0.00728183023772, -0.00073155573939),
                   'R4': (-0.02490747037406, 0.26363266501679, -0.07330346656184, 0.01876886839392, -0.00176688757979),
                   'R5': (-0.19423148776489, 0.45952477474223, -0.18163820209523, 0.04173579115885, -0.00355426505742),
                   'R6': (0.04574408690798, -0.05092121193598, 0.13874539944789, -0.04344815868749, 0.00449747222180),
                   'R1range': (498, 3915),
                   'R2range': (498, 3915),
                   'R3range': (498, 3915),
                   'R4range': (907, 3915),
                   'R5range': (1219, 3915),
                   'R6range': (1559, 3915)
                   }

    coeff['1S'] = {'R1': (-0.01040584267474, 0.53121149663696, 0.00576913817747, -0.00039325152252, -0.00007954180489),
                   'R2': (0.37339166598255, -0.15814640001919, 0.24085046064819, -0.06068695741919, 0.00563606634601),
                   'R3': (0.06969331604484, 0.28154425636993, -0.08121643989151, 0.02372741957255, -0.00238998426027),
                   'R4': (0.04462649178239, 0.23204790123388, -0.06083969521863, 0.01564282892512, -0.00145145206815),
                   'R5': (-0.20727547407753, 0.53536509500863, -0.22521649838170, 0.05180965157326, -0.00439750995163),
                   'R6': (0.27169670700251, -0.37192045082925, 0.31939855191976, -0.08668833166842, 0.00822975581940),
                   'R1range': (530, 3947),
                   'R2range': (530, 3947),
                   'R3range': (530, 3947),
                   'R4range': (939, 3947),
                   'R5range': (1251, 3947),
                   'R6range': (1591, 3947)
                   }

    coeff['2S'] = {'R1': (-0.01937823810470, 0.53084210514216, 0.00580573751882, -0.00038281138203, -0.00007958217070),
                   'R2': (0.68496829280011, -0.54558176102022, 0.44926662609767, -0.11154849560657, 0.01023294598884),
                   'R3': (0.04215807391059, 0.40434195078925, -0.15884974959493, 0.04319968814535, -0.00413693825139),
                   'R4': (0.14015578207913, 0.14407679007180, -0.01310480312503, 0.00362292256563, -0.00034189078786),
                   'R5': (-0.02549241716294, 0.32153542852101, -0.11409513283836, 0.02617210469576, -0.00221816103608),
                   'R6': (-0.14490868030324, 0.33629928307361, -0.08223564735018, 0.01023410734015, -0.00027717589598),
                   'R1range': (562, 3978),
                   'R2range': (562, 3978),
                   'R3range': (562, 3978),
                   'R4range': (971, 3978),
                   'R5range': (1283, 3978),
                   'R6range': (1623, 3978)
                   }

    def ratio(self, mass: float, sulfurs: str, ratio: str):

        b = self.coeff[sulfurs][ratio]

        return b[ratio][0] + b[ratio][1]*(mass/1000) + b[ratio][2]*(mass/1000)**2 + b[ratio][3]*(mass/1000)**3 +\
               b[ratio][4]*(mass/1000)**4

    def generate_profiles(self, mass: float):

        R1S0 = self.ratio(mass=mass, sulfurs='S0', ratio='R1')
        R2S0 = self.ratio(mass=mass, sulfurs='S0', ratio='R2')
        R3S0 = self.ratio(mass=mass, sulfurs='S0', ratio='R3')
        R4S0 = self.ratio(mass=mass, sulfurs='S0', ratio='R4')
        R5S0 = self.ratio(mass=mass, sulfurs='S0', ratio='R5')
        R6S0 = self.ratio(mass=mass, sulfurs='S0', ratio='R6')

        R1S1 = self.ratio(mass=mass, sulfurs='S1', ratio='R1')
        R2S1 = self.ratio(mass=mass, sulfurs='S1', ratio='R2')
        R3S1 = self.ratio(mass=mass, sulfurs='S1', ratio='R3')
        R4S1 = self.ratio(mass=mass, sulfurs='S1', ratio='R4')
        R5S1 = self.ratio(mass=mass, sulfurs='S1', ratio='R5')
        R6S1 = self.ratio(mass=mass, sulfurs='S1', ratio='R6')

        R1S2 = self.ratio(mass=mass, sulfurs='S2', ratio='R1')
        R2S2 = self.ratio(mass=mass, sulfurs='S2', ratio='R2')
        R3S2 = self.ratio(mass=mass, sulfurs='S2', ratio='R3')
        R4S2 = self.ratio(mass=mass, sulfurs='S2', ratio='R4')
        R5S2 = self.ratio(mass=mass, sulfurs='S2', ratio='R5')
        R6S2 = self.ratio(mass=mass, sulfurs='S2', ratio='R6')

        return {'S1': np.asarray((1, R1S0, R2S0, R3S0, R4S0, R5S0, R6S0), float),
                'S2': np.asarray((1, R1S1, R2S1, R3S1, R4S1, R5S1, R6S1), float),
                'S3': np.asarray((1, R1S2, R2S2, R3S2, R4S2, R5S2, R6S2), float)}

    def match(self, parent_mass: float, spectrum: np.ndarray):

        data = spectrum[(spectrum[:, 0] > parent_mass - 5) & (spectrum[:, 0] < parent_mass + 5), :2]

        scores = dict()

        for mass, intensity in data:

            profiles = self.generate_profiles(mass=mass)

            # profile_score = dict()

            for charge in range(1, 5):

                masses = [mass + 1.003356/charge*x for x in range(7)]

                matching_spectrum = np.asarray([data[np.argmin(data[:, 0] - x), :] for x in masses], float)

                for sulfur in ('S1', 'S2', 'S3'):

                    intensities = [intensity*profiles[sulfur]]

                    score = np.asarray((masses, intensities)).transpose()
