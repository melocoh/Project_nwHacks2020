from ghapi import GhApi
github_access_token = '7386ec7242c169af34743d690a253a4d6cc724aa'
api = GhApi(token = github_access_token)
print(api.rate_limit.get())