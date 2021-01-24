from rest_framework import serializers

# example response:
# 
# {
#     "files": [{
#         "name": "text/example.py",
#         "lines": [{
#             "text": "import thing",
#             "is_covered": True,
#             "is_critical": True
#         }]
#     }]
# }

# models
class CriticalPathLine(object):
    # we will update the worker to manage line counts
    def __init__(self, lineno, count=1):
        self.lineno = lineno
        self.count = count

class CriticalPathFile(object):
    def __init__(self, name, lines):
        self.name = name
        self.lines = lines

class CriticalPathResponse(object):
    def __init__(self, files):
        self.files = files

# serializers
class CriticalPathLineSerializer(serializers.Serializer):
    lineno = serializers.IntegerField()
    count = serializers.IntegerField()

class CriticalPathFileSerializer(serializers.Serializer):
    name = serializers.CharField()
    lines = CriticalPathLineSerializer(many=True)

class CriticalPathResponseSerializer(serializers.Serializer):
    files = CriticalPathFileSerializer(many=True)
