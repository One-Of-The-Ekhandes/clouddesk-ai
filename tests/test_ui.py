from streamlit.testing.v1 import AppTest


def test_streamlit_app_triages_an_example():
    at = AppTest.from_file("../app/streamlit_app.py", default_timeout=30).run()
    assert not at.exception
    at.selectbox[0].select(at.selectbox[0].options[2]).run()  # the Lambda AccessDenied example
    at.button[0].click().run()
    assert not at.exception
    assert [m.value for m in at.metric] == ["cloud access", "cloud team", "Yes"]
