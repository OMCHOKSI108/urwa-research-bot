import re

# Read the file
with open('app/models/data_schemas.py', 'r') as f:
    content = f.read()

# Replace all Config classes with ConfigDict
content = re.sub(r'    class Config:\s*extra = "allow"', '    model_config = ConfigDict(extra="allow")', content, flags=re.MULTILINE)

# Write back
with open('app/models/data_schemas.py', 'w') as f:
    f.write(content)

print('Updated all Config classes to ConfigDict')