from pylb.experiments.pytest import add

def test_add():
    assert add(1,2) == 3

def test_failthisadd():
    assert add(1,2) == 4
    

