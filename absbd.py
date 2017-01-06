import os, sys, glob, subprocess, json

if __name__ == '__main__':
    workdir = os.getcwd()
    #fetch all the configuration files
    files = glob.glob('*absbd_config.json')
    #load files to handle dependencies
    configs = {}
    for fn in files:
        with open(fn,'r') as f:
            configs[fn] = json.loads(f.read())
    #compute dependency order
    dep_ids = set([-1])
    dep_mapping = {}

    def _compute_dependencies(fn, configs, dep_mapping, dep_ids):
        if fn in dep_mapping:
            return dep_mapping, dep_ids
        elif "dependencies" in configs[fn]:
            deps = set(glob.glob(configs[fn]["dependencies"]))
            deps.discard(fn)
            for dep in deps:
                dep_mapping, dep_ids = _compute_dependencies(dep, configs, dep_mapping, dep_ids)
        dep_mapping[fn] = max(dep_ids)+1
        dep_ids.add(max(dep_ids)+1)
        return dep_mapping, dep_ids

    for fn in configs.keys():
        dep_mapping, dep_ids = _compute_dependencies(fn, configs, dep_mapping, dep_ids)

    order = configs.keys()
    order.sort(key = lambda x:dep_mapping[x])

    #we dump all the config files in a single json document at the top level, so other commands can access the metadata
    with ("absbd_all_configs.json",'w') as f:
        f.write(json.dumps(configs))

    #now that we have the order of items, we execute the command for each item.
    for fn in order:
        #by default, the command is called from the root directory.  If you want path interpolation, use the {loc}, {configs} or {root} block in your command
        #run_loc allows you to change the working directory
        location = os.path.dirname(fn)
        configs_path = os.path.join(workdir, "absbd_all_configs.json")
        run_data = configs[fn]["run"]
        run_dir = None
        try:
            run_dir = run_data["location"].format(loc=location, root=workdir, configs=configs_path)
            run_command = run_data["command"].format(loc=location, root=workdir, configs=configs_path)
            os.chdir(run_dir)
        except KeyError:
            run_command = run_data.format(loc=location, root=workdir, configs=configs_path)
        subprocess.call(run_command, shell=True)
        if run_dir != None:
            os.chdir(workdir)
