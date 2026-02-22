@echo off
REM ============================================
REM  일일 스크리닝 자동 실행 (Windows Task Scheduler용)
REM
REM  설정 방법:
REM  1. Win+R → taskschd.msc
REM  2. "기본 작업 만들기" 클릭
REM  3. 이름: "Stock Advisor Daily Screen"
REM  4. 트리거: 매일, 오전 7:00 (미국 장 시작 전)
REM  5. 동작: 프로그램 시작
REM     - 프로그램: 이 파일의 전체 경로
REM     - 시작 위치: 이 파일이 있는 폴더
REM  6. "마침" → 속성에서 "컴퓨터가 AC 전원일 때만" 해제 권장
REM ============================================

cd /d "%~dp0"
python -m scheduler.daily_screener
