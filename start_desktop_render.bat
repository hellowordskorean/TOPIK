@echo off
:: Hellowords 데스크탑 렌더링 워처 자동 시작
:: 이 파일을 Windows 시작 프로그램에 등록하세요:
::   Win+R → shell:startup → 이 파일의 바로가기 붙여넣기

cd /d Z:\Hellowords\youtube
start /min pythonw desktop_render.py
