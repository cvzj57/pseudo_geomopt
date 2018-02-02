#!/usr/bin/python3
import subprocess
import math

# Old Ethane fit
'''
no_atoms = 8
a = 0.484478
b = 1.68407
x0 = 2.41293
factor = 1.0
'''

# Staggered Ethane fit (new basis)
'''
no_atoms = 8
a = 0.470363
b = 1.67927
x0 = 2.43377
factor = 1.0
'''


# Eclipsed Ethane fit (new basis)
'''
no_atoms = 8
a = 0.472942
b = 1.68207
x0 = 2.43729
factor = 1.0
'''


# Ethene fit (new basis)

no_atoms = 8
a = 3.48487
b = 1.94326
c = -2.72191
x0 = 1.74196
factor = 1.0

'''
# Ethene fit (new basis)
no_atoms = 8
a = 368.126
b = 0.169015
c = -2.70009
x0 = -3.53757
factor = 1.0
'''


def calculate_gradient_correction(dcc):
    return -b * a * math.exp(-b*(dcc - x0))
    #return 2 * -b * a * (dcc-x0) * math.exp(-b*(dcc - x0)**2)


def calculate_energy_correction(dcc):
    # return a * math.exp(-b*(dcc - x0))
    return a * math.exp(-b*(dcc - x0)) + c
    #return a * math.exp(-b*(dcc - x0)**2) + c


log_file = open('cheating.log', 'w+')
log_file.writelines("Attempting to correct gradient...\n\n")


#  Get c c distance and find correction
distance_output = subprocess.check_output(['dist', 'c', 'c'], universal_newlines=True)
distance_cc = float(distance_output.split()[7])
log_file.writelines('dist output: ' + distance_output)
gradient_correction = calculate_gradient_correction(distance_cc)
energy_correction = calculate_energy_correction(distance_cc)

#  Get gradient
gradient_file = open('gradient', 'r')
gradient_file_data = gradient_file.readlines()
gradient_file.close()
dEdZ_line1_raw = gradient_file_data[-1-no_atoms]
dEdZ_line2_raw = gradient_file_data[-no_atoms]
dEdZ_line1 = dEdZ_line1_raw.split()
dEdZ_line2 = dEdZ_line2_raw.split()
log_file.writelines('1st atom gradient: ' + dEdZ_line1_raw + '\n')
log_file.writelines('2nd atom gradient: ' + dEdZ_line2_raw + '\n')
dEdZ1 = float(dEdZ_line1[2].replace('D', 'e'))
dEdZ2 = float(dEdZ_line2[2].replace('D', 'e'))
new_dEdZ1 = dEdZ1 + factor*gradient_correction
new_dEdZ2 = dEdZ2 - factor*gradient_correction

#  Get energy
energy_line_raw = None
for gradient_file_line in reversed(gradient_file_data):
    if gradient_file_line.strip()[:5] == "cycle":
        energy_line_raw = gradient_file_line
        break
energy_line = energy_line_raw.split()
log_file.writelines('Cycle line: ' + energy_line_raw + '\n')
energy = float(energy_line[6])
new_energy_string = str(energy + energy_correction)


def translate_into_fortran(dEdZ):
    new_dE_string = dEdZ
    if dEdZ[0] == '-' and dEdZ[2] == '.':
        if dEdZ[-1] == '0':
            new_ending = 1
        elif dEdZ[-3] == '+':
            new_ending = int(dEdZ[-1]) + 1
        elif dEdZ[-3] == '-':
            new_ending = int(dEdZ[-1]) - 1
        new_beginning = dEdZ[0] + '.' + dEdZ[1]
        new_dE_string = new_beginning + dEdZ[3:-1] + str(new_ending)
        log_file.writelines("Translated into FORTRAN: %s\n" % new_dE_string)
    return new_dE_string


#  Translate from sensible formatting into FORTRAN
new_dE_string1 = ("%e" % new_dEdZ1).replace('e', 'D')
new_dE_string2 = ("%e" % new_dEdZ2).replace('e', 'D')
log_file.writelines("New dE strings: %s %s\n" % (new_dE_string1, new_dE_string2))
new_dE_string1 = translate_into_fortran(new_dE_string1)
new_dE_string2 = translate_into_fortran(new_dE_string2)

#  Insert new gradients
gradient_file_data.insert(-1-no_atoms, '  %s  %s  %s\n' % (
    dEdZ_line1[0],
    dEdZ_line1[1],
    new_dE_string1)
)
gradient_file_data.insert(-1-no_atoms, '  %s  %s  %s\n' % (
    dEdZ_line2[0],
    dEdZ_line2[1],
    new_dE_string2)
)

#  Insert new energy
log_file.writelines("cycle line index: %s\n" % str(gradient_file_data.index(energy_line_raw)))
gradient_file_data.insert(-2*no_atoms-3, '  %s  %s  %s %s %s %s %s %s %s %s\n' % (
    energy_line[0],
    energy_line[1],
    energy_line[2],
    energy_line[3],
    energy_line[4],
    energy_line[5],
    new_energy_string,
    energy_line[7],
    energy_line[8],
    energy_line[9]
)
)
#
# #zero hydrogens
# gradient_file_data.insert(-1-no_atoms, '  %s  %s  %s\n' % (
#     '0.0D+00',
#     '0.0D+00',
#     '0.0D+00')
# )
# gradient_file_data.insert(-1-no_atoms, '  %s  %s  %s\n' % (
#     '0.0D+00',
#     '0.0D+00',
#     '0.0D+00')
# )


# h1_line1_raw = gradient_file_data[-no_atoms+1]
# h2_line2_raw = gradient_file_data[-no_atoms+2]
# gradient_file_data.remove(h1_line1_raw)
# gradient_file_data.remove(h2_line2_raw)

gradient_file_data.remove(dEdZ_line1_raw)
gradient_file_data.remove(dEdZ_line2_raw)
gradient_file_data.remove(energy_line_raw)
with open('gradient', 'w') as gradient_file:
    gradient_file.writelines(gradient_file_data)
gradient_file.close()

log_file.writelines('''Gradient correction performed:\n
                    dcc: %s\n
                    gradient correction: %s\n 
                    new gradient 1: %s\n
                    new gradient 2: %s\n
                    new gradient 1 string: %s\n
                    new gradient 2 string: %s\n
                    old energy: %s\n                    
                    new energy: %s\n                    
'''
                    % (distance_cc, gradient_correction, new_dEdZ1, new_dEdZ2,
                       new_dE_string1, new_dE_string2, str(energy), new_energy_string))
log_file.close()

#  Run statpt
subprocess.call('/share/programs/COSMOlogic/TmoleX17/TURBOMOLE/bin/em64t-unknown-linux-gnu/relax', shell=False)
