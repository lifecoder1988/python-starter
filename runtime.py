


from bottle import request,route, run, template

import json

import sys


import function

def getApiConfig(name):
    with open("./api2.json", 'r') as load_f:
        load_dict = json.load(load_f)
        print(load_dict)
        return load_dict

@route('/<name>')
def index(name):

    apiConfig = getApiConfig(name)
    return runApi(request,apiConfig)
    #print(name)

def checkPrivilege(request,api):
    print("checkPrivilege")
    if "privilege" in api :
        print("check api is fine for ...")
        print(api["privilege"])
    else:
        print("unsafe : api is open")

def parseRequest(request,apiRequest) :

    print("parseRequest")
    data = {}

    print("request ===== ")
    print(request)

    print("parseRequest parse headers")

    for item in apiRequest["headers"]:
        key = item["name"]
        request.headers.get(key)
        data[key] = request.headers.get(key)

    print("parseRequest parse body")

    for item in apiRequest["body"]:
        key = item["name"]
        if request.json and key in request.json:
            data[key] = request.json[key]
        else:
            print("key %s not exist in request json" %key)

    print("parseRequest parse params")

    for item in apiRequest["params"]:
        key = item["name"]
        data[key] = request.query.get(key)

    return data


def getRequestDataByVar(v,data):


    if isinstance(v,str) and v[0] == '$':
        key = v[1:]
        if key in data:
            return data[key]
        return None
    return v

def updateRequestDataByVar(v,value,data):
    if v[0] != '$':
        raise Exception("var must start with $")
    key = v[1:]
    if key in data:
        data[key] = value
    else:
        print("key not exist")


def getFuncParams(paramDict,requestData):
    params = {}
    for k,v in paramDict.items():
        params[k] = getRequestDataByVar(v,requestData)
    return params


def processCheckFunc(func,requestData):
    print("processCheckFunc")
    func_name = func['name']
    func_params = getFuncParams(func['params'],requestData)

    print(dir(function))
    f = getattr(function,func_name,None)

    print(func_params)

    checked = f(**func_params)
    if checked == False:
        raise Exception(func)

def processFormatFunc(func,requestData):
    print("processFormatFunc")
    func_name = func['name']
    func_params = getFuncParams(func['params'], requestData)

    f = getattr(function, func_name, None)

    formatted = f(**func_params)
    return formatted


def getSqlByTemplate(tpl,data):
    print("getSqlByTemplate")
    print(data)
    for k,v in data.items():
        if v != None:
            tpl = tpl.replace("$"+k,v)
    return tpl

def doQuery(query,requestData):
    print("doQuery")
    print(query["db"])
    sql = getSqlByTemplate(query["sql"],requestData)
    print(sql)

def callMiniAPI(requestData,miniapi):
    print("callMiniAPI")
    print(miniapi)


def doSQLProcess(requestData,processData) :
    print("doSQLProcess")
    for func in processData["check_func"]:
        processCheckFunc(func,requestData)
    for func in processData["format_func"]:
        formatted = processFormatFunc(func,requestData)
        updateRequestDataByVar(func["modify"],formatted,requestData)

    result = doQuery(processData["query"],requestData)
    return result

def doProxyProcess(requestData,processData) :
    print("doProxyProcess")
    result = {}
    for miniapi in processData["api"]:
        ## 这里可以改成并发
        key = miniapi["key"]
        result[key] = callMiniAPI(requestData,miniapi)
    return result

def doProcess(requestData,processData):
    print("doProcess")
    if processData["type"] == "sql":
        return doSQLProcess(requestData,processData)
    elif processData["type"] == "proxy":
        return doProxyProcess(requestData, processData)
    else :
        print("type not support")

    return False


def doReponseFunc(data,apiResponse):
    code = apiResponse['response_func']
    codeFile = open("tmpLib.py", "w")
    codeFile.writelines(code)
    codeFile.close()
    __import__("tmpLib")
    print(sys.modules['tmpLib'])

    f = getattr(sys.modules['tmpLib'], "hellWord", None)
    return f(data)

def jsonResponse(data) :
    return json.dumps({"code":0,"msg":"","data":data})

def jsonException(e):
    return json.dumps({"code": -1, "msg": "exception", "data": ""})

def runApi(request,api):

    try:
        checkPrivilege(request,api)
        requestData = parseRequest(request,api["request"])
        if "process" in api:
            data = doProcess(requestData,api["process"])
        if "response" in api:
            data = doReponseFunc(data,api["response"])
        return jsonResponse(data)
    except e:
        print(e)
        return jsonException(e)



run(host='localhost', port=8080)