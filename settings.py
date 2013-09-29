MATCHER_BASE_URL = 'http://localhost:8001'


# Attempt to load overriding settings from settingslocal.
try:
    import settingslocal
except ImportError:
    settingslocal = None

if settingslocal:
    for setting in dir(settingslocal):
        globals()[setting.upper()] = getattr(settingslocal, setting)
