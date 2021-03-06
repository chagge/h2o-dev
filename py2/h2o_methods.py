
import os, sys, time, requests, zipfile, StringIO, re
import h2o_args
# from h2o_cmd import runInspect, infoFromSummary
import h2o_cmd, h2o_util
import h2o_browse as h2b

from h2o_objects import H2O
from h2o_test import verboseprint, dump_json, check_sandbox_for_errors, get_sandbox_name, log

# print "h2o_methods"

# this is done before import h2o_ray, which imports h2o_methods!
# ignoreNone is used if new = None shouldn't overwrite. Normally it does!
def check_params_update_kwargs(params_dict, kw, function, print_params, ignoreNone=False):
    # only update params_dict..don't add
    # throw away anything else as it should come from the model (propagating what RF used)
    for k,v in kw.iteritems():
        if k in params_dict:
            if v or not ignoreNone:
                # what if a type conversion happens here? (checkHeader = -1 overwriting an existing value?)
                params_dict[k] = v
        else:
            raise Exception("illegal parameter '%s' with value '%s' in %s" % (k, v, function))

    if print_params:
        print "\n%s parameters:" % function, params_dict
        sys.stdout.flush()


def get_cloud(self, noExtraErrorCheck=False, timeoutSecs=10):
    # hardwire it to allow a 60 second timeout
    a = self.do_json_request('Cloud.json', noExtraErrorCheck=noExtraErrorCheck, timeout=timeoutSecs)
    # verboseprint(a)

    version    = a['version']
    if not version.startswith('0'):
        raise Exception("h2o version at node[0] doesn't look like h2o-dev version. (start with 0) %s" % version)

    consensus = a['consensus']
    locked = a['locked']
    cloud_size = a['cloud_size']
    cloud_name = a['cloud_name']
    node_id = self.node_id
    verboseprint('%s%s %s%s %s%s %s%s %s%s' % (
        "\tnode_id: ", node_id,
        "\tcloud_size: ", cloud_size,
        "\tconsensus: ", consensus,
        "\tlocked: ", locked,
        "\tversion: ", version,
    ))
    return a

def h2o_log_msg(self, message=None, timeoutSecs=15):
    if not message:
        message = "\n"
        message += "\n#***********************"
        message += "\npython_test_name: " + h2o_args.python_test_name
        message += "\n#***********************"
    params = {'message': message}
    self.do_json_request('2/LogAndEcho.json', params=params, timeout=timeoutSecs)

def get_timeline(self):
    return self.do_json_request('Timeline.json')

# Shutdown url is like a reset button. Doesn't send a response before it kills stuff
# safer if random things are wedged, rather than requiring response
# so request library might retry and get exception. allow that.
def shutdown_all(self):
    try:
        self.do_json_request('Shutdown.json', noExtraErrorCheck=True)
    except:
        print "Got exception on Shutdown.json. Ignoring"
        pass
    # don't want delayes between sending these to each node
    # if you care, wait after you send them to each node
    # Seems like it's not so good to just send to one node
    # time.sleep(1) # a little delay needed?
    return (True)


#*******************************************************************************
def jobs_admin (self, *args, **kwargs):
    print "WARNING: faking jobs admin"
    a = { 'jobs': {} }
    return a

def unlock (self, *args, **kwargs):
    print "WARNING: faking unlock keys"
    pass

def remove_all_keys(self, timeoutSecs=120):
    return self.do_json_request('RemoveAll.json', timeout=timeoutSecs)

def rapids(self, timeoutSecs=120, **kwargs):
    params_dict = {
        'ast': None,
        'fun': None,
    }

    def quotewrap(ast):
        if ast not in kwargs: return None
        if not kwargs[ast]: return None
        
        astv = kwargs[ast]
        r1 = re.compile(r"'.*'$") # surrounded with single quote
        r2 = re.compile(r'".*"$') # surrounded with double quote
        if r1.match(astv):
            pass
        elif r2.match(astv):
            pass
        elif "'" in astv and '"' in astv:
            raise Exception("Mixed single and double quote in ast, but not wrapped with one or the other %s" % astv)
        elif "'" in astv: # can wrap in double quote
            astv = '"' + astv + '"'
        else: # can wrap in single quote
            astv = "'" + astv + "'"
        print "astv:", astv
        return astv
    

    # surround the ast with single quote if not there?
    kwargs['ast'] = quotewrap('ast')
    kwargs['fun'] = quotewrap('fun')
    check_params_update_kwargs(params_dict, kwargs, 'rapids', True)

    result = self.do_json_request('Rapids.json', timeout=timeoutSecs, params=params_dict)
    return result

def csv_download(self, key, csvPathname, timeoutSecs=60, **kwargs):
    params = {
        'key': key
    }

    paramsStr = '?' + '&'.join(['%s=%s' % (k, v) for (k, v) in params.items()])
    url = self.url('DownloadDataset.json')
    log('Start ' + url + paramsStr, comment=csvPathname)

    # do it (absorb in 1024 byte chunks)
    r = requests.get(url, params=params, timeout=timeoutSecs)
    print "csv_download r.headers:", r.headers
    if r.status_code == 200:
        f = open(csvPathname, 'wb')
        for chunk in r.iter_content(1024):
            f.write(chunk)
    else:
        raise Exception("unexpected status for DownloadDataset: %s" % r.status_code)

    print csvPathname, "size:", h2o_util.file_size_formatted(csvPathname)

#******************************************************************************************8
# attach methods to H2O object
# this happens before any H2O instances are created
# this file is imported into h2o

H2O.get_cloud = get_cloud
H2O.h2o_log_msg = h2o_log_msg
H2O.jobs_admin = jobs_admin
H2O.rapids = rapids
H2O.unlock = unlock
H2O.get_timeline = get_timeline
H2O.csv_download = csv_download
H2O.remove_all_keys = remove_all_keys
# H2O.shutdown_all = shutdown_all

# attach some methods from ray
import h2o_ray
H2O.jobs = h2o_ray.jobs
H2O.poll_job = h2o_ray.poll_job
H2O.import_files = h2o_ray.import_files
H2O.parse = h2o_ray.parse
H2O.frames = h2o_ray.frames
H2O.columns = h2o_ray.columns
H2O.column = h2o_ray.column
H2O.summary = h2o_ray.summary
H2O.delete_frame = h2o_ray.delete_frame
H2O.delete_frames = h2o_ray.delete_frames
H2O.model_builders = h2o_ray.model_builders
H2O.validate_model_parameters = h2o_ray.validate_model_parameters
H2O.build_model = h2o_ray.build_model
H2O.compute_model_metrics = h2o_ray.compute_model_metrics
H2O.predict = h2o_ray.predict
H2O.model_metrics = h2o_ray.model_metrics
H2O.models = h2o_ray.models
H2O.delete_model = h2o_ray.delete_model
H2O.delete_models = h2o_ray.delete_models
H2O.endpoints = h2o_ray.endpoints
H2O.endpoint_by_number = h2o_ray.endpoint_by_number
