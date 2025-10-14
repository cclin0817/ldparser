import subprocess
import argparse
import pickle
import pandas as pd
from tqdm import tqdm
parser = argparse.ArgumentParser(description='given def path, return instance/net dict to -o ')
parser.add_argument('--def_lef_folder', type = str, default="../tmp" )
parser.add_argument('--net_cell_mat_path', type = str, default="./tmp/net_cell_mat.pkl" )
parser.add_argument('--net_2_block_path', type = str, default="./tmp/net_2_block.pkl" )
parser.add_argument('--test_mode', type = bool, default=False  ) # False, True

args = parser.parse_args()
net_cell_mat_path = args.net_cell_mat_path
net_2_block_path = args.net_2_block_path
output_dir = args.def_lef_folder

with open(output_dir + '/def_outputs.pkl', 'rb') as file:
    def_output = pickle.load( file)
with open(output_dir + '/lef_outputs.pkl', 'rb') as file:
    lef_output = pickle.load( file)

id2instanceInfo = def_output['id2instanceInfo']
instance2id = def_output['instance2id']
net2id = def_output['net2id']
id2NetInfo = def_output['id2NetInfo']

cell_dict = lef_output['cell_dict']

def net_cell_mat_gen():
    net_2_block = {}
    mat_collector = []
    for index in tqdm(id2NetInfo.keys()):
        piece = id2NetInfo[index]
        if len(piece['connections']) == 1:
            continue
        
        net_block = []

        for connect in piece['connections']:
            assert connect['instance_name'] == id2instanceInfo[instance2id[connect['instance_name']]]['instance_name']
            cell_name = id2instanceInfo[instance2id[connect['instance_name']]]['cell_name']
            pin_name = connect['pin_name']
            
            if 'direction' not in cell_dict[cell_name]['pins'][pin_name]:
                print('direction not in ', cell_name, pin_name)
                continue
            
            if cell_dict[cell_name]['pins'][pin_name]['direction'] == 1:
                ds_symbole = ">"
            elif cell_dict[cell_name]['pins'][pin_name]['direction'] == -1:
                ds_symbole = "<"
            else:
                assert NotImplementedError
            
            row = {
                'i': index,
                'j': instance2id[connect['instance_name']],
                'instance_name': connect['instance_name'],
                'net_name_set': set([piece['net_name']]),
                'pin_name': pin_name,
                'cell_name': cell_name,
                'DS': cell_dict[cell_name]['pins'][pin_name]['direction'],
                'l_cell': f'{cell_name}@{pin_name}{ds_symbole}'
            }
            mat_collector.append(row)
            net_block.append(row)
        net_2_block[piece['net_name']] = pd.DataFrame(net_block)
    net_cell_mat = pd.DataFrame(mat_collector)
    return net_cell_mat, net_2_block

def net_instance_dict_gen():
    net_instance_dict = {}
    for index in tqdm(id2NetInfo.keys()):
        
        piece = id2NetInfo[index]
        
        if len(piece['connections']) == 1:
            print(piece['net_name'], len(piece['connections']))
            # breakpoint()
            continue
        driver_collect = []
        sin_collect = []
        
        for connect in piece['connections']:
            try:
                assert connect['instance_name'] == id2instanceInfo[instance2id[connect['instance_name']]]['instance_name']
            except:
                breakpoint()
            cell_name = id2instanceInfo[instance2id[connect['instance_name']]]['cell_name']
            pin_name = connect['pin_name']
            
            if cell_name not in cell_dict:
                breakpoint()
            if 'direction' not in cell_dict[cell_name]['pins'][pin_name]:
                # breakpoint()
                print(cell_name, pin_name ,'have no direction')
                continue
            # else:
            #     breakpoint()
            
            if cell_dict[cell_name]['pins'][pin_name]['direction'] == 1:
                driver_collect.append(connect['instance_name'])
                
            elif cell_dict[cell_name]['pins'][pin_name]['direction'] == -1:
                sin_collect.append(connect['instance_name'])
                
            else:
                assert NotImplementedError
        net_instance_dict[piece['net_name']] = (tuple(driver_collect), tuple(sin_collect) )
    return net_instance_dict

net_instance_dict = net_instance_dict_gen()
net_cell_mat, net_2_block = net_cell_mat_gen()
with open(net_cell_mat_path, 'wb') as file:
    pickle.dump(net_cell_mat, file)
with open(net_2_block_path, 'wb') as file:
    pickle.dump(net_2_block, file)

'''

def_output = {
    'instance2id': instance2id,
    'id2instanceInfo': id2instanceInfo,
    'net2id': net2id,
    'id2NetInfo': id2NetInfo
}

lef_output = {
    'cell_dict': cell_dict
}


'''


