try:
    exec(open('app/services/eligibility.py').read())
    print('EligibilityEngine' in dir())
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
