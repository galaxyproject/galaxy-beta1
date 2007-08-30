#build list of available data
import os, sys
maf_sets = {}

try:
    for line in open( "/depot/data2/galaxy/maf_index.loc" ):
        if line[0:1] == "#" : continue
        
        fields = line.split('\t')
        #read each line, if not enough fields, go to next line
        try:
            maf_desc = fields[0]
            maf_uid = fields[1]
            builds = fields[2]
            build_list =[]
            split_builds = builds.split(",")
            for build in split_builds:
                this_build = build.split("=")[0]
                build_list.append(this_build)
            paths = fields[3].replace("\n","").replace("\r","")
            maf_sets[maf_uid]={}
            maf_sets[maf_uid]['description']=maf_desc
            maf_sets[maf_uid]['builds']=build_list
        except:
            continue

except Exception, exc:
    print >>sys.stdout, 'maf_stats_code.py initialization error -> %s' % exc 

#return available datasets for group and build, set None option as selected for hg16
def get_available_data( build ):
    available_sets = []
    for key in maf_sets:
        if build in maf_sets[key]['builds']:
            available_sets.append((maf_sets[key]['description'],key,False))
    if len(available_sets) < 1:
        available_sets.append(('No data available for this build','None',True))
    return available_sets


def exec_before_job(app, inp_data, out_data, param_dict, tool):
    if param_dict['maf_source_type']['maf_source'] == "cached":
        for name, data in out_data.items():
            try:
                data.name = data.name + " [" + maf_sets[str(param_dict['maf_source_type']['mafType'])]['description'] + "]"
            except KeyError:
                data.name = data.name + " [unknown MAF source specified]"
    if param_dict['summary'].lower() == "true":
        for name, data in out_data.items():
            data.change_datatype('tabular')
