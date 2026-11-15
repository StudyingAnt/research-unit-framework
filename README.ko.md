# Research Program Framework

**언어:** [English](README.md) | 한국어  
**바로 가기:** [프로젝트 템플릿](template/) · [설계 철학 (한국어)](docs/PHILOSOPHY.ko.md) · [Design Philosophy (English)](docs/PHILOSOPHY.md)

연구자가 주도하는 생명과학 연구를 위한 가벼운 프로젝트 템플릿입니다. [`template/`](template/)에서 실제 생성할 프로젝트 구조를 확인할 수 있습니다. Markdown 작업 지침, Coordination 계획, Aim/Strategy/Tactic(AST) 작업, 상세한 영문·국문 보고서와 소수의 실용적인 Python 스크립트로 구성됩니다.

**2.0은 새로운 기준 버전입니다.** v1.1의 과학적 설계를 계승하지만 이전 Framework 설치를 자동 전환하거나 과거 버전과의 호환성을 보장하지 않습니다. 기존 연구는 그대로 두고, 필요할 때 개별적으로 참고할 수 있습니다.

## 새 프로젝트 만들기

Linux/WSL과 Python 3.9 이상에서 프로젝트 생성 및 업데이트를 사용할 수 있습니다. 저장소를 복제하거나 릴리스를 추출한 뒤 처음 한 번 Framework 루트를 `PATH`에 추가합니다.

```bash
export PATH="/absolute/path/to/research-unit-framework:$PATH"
newproj --configure ~/projects
newproj my_research
```

계속 사용하려면 `export`를 셸 구성 파일에도 추가하세요. 기본 프로젝트 상위 폴더는 `~/projects`이며 `RPF_PROJECTS_DIR` 또는 `--projects-dir`로 변경할 수 있습니다.

```bash
newproj my_research --destination /absolute/path/to/my_research
```

`PATH`를 설정하지 않으려면 Framework 저장소에서 `python3 tools/newproj.py my_research`를 실행하세요. 이미 존재하는 대상에 생성하지 않으며, Git 저장소·과학 환경·연구 방향·AST를 자동으로 만들지 않습니다.

## Coordination 시작하기

생성된 프로젝트를 Codex나 다른 연구 보조 도구에서 열고 다음과 같이 시작합니다.

> Start Coordination. Research Map과 관련 계획서를 읽고 현재 질문, 가설, 대안, 우선순위를 함께 검토해 주세요.

AI는 `AGENTS.md`와 `coordination/COORDINATION.md`를 읽어 Narrative, Workstream, Aim, 의존관계와 논문에 연결할 증거를 논의합니다. 취약한 가정과 부족한 증거를 적극적으로 지적하되 **연구자가 명시적으로 승인한 결정만** 공식 기록에 반영합니다. 자유로운 토론만으로 AST나 가설이 확정되지 않습니다.

## AST 세션 시작 및 재개

AI에게 관련 계획서를 읽고 Aim, Strategy, 제한된 Tactic 질문과 상세 Specifications를 함께 정하도록 요청합니다. 승인 후 `tools/new_unit.py`로 ID와 폴더를 생성합니다. 명령어를 연구자가 외울 필요는 없습니다.

중단된 작업은 기존 `A###-S##-T##` ID로 재개합니다. 보고서를 여러 번 개정해도 같은 AST이며 실질적으로 새로운 증거 생산 질문일 때 새로운 Tactic을 만듭니다. 개별 실행 `R###` Run은 선택 사항입니다.

Coordination과 AST 세션은 **저장된 계획서, 보고서, Figure를 통해** 연구 맥락을 공유합니다. 채팅 간 직접 메시지나 의무적인 인계 요약은 필요하지 않습니다. 분석 코드는 `repos/`의 독립 저장소에서 관리할 수 있으며 물리적 연구와 원격 HPC는 사람이 수행합니다. 과거 연구의 일괄 변환도 필요하지 않습니다.

## 보고서 만들기

11개 섹션의 영문·국문 보고서에는 연구 배경, 정의, 실제 절차, 필터, 계산, 대조군, 불확실성, 설정, Figure/표, 결과, 해석, 한계, 출처를 기록합니다. **Methods는 코드를 열지 않고도 과학적 방법을 검토할 수 있을 만큼 상세해야 하며, 페이지 제한은 없습니다.**

Markdown을 편집하고, 별도로 설정한 Pandoc 및 `requirements/reporting.txt`의 Python 패키지와 적절한 로컬 폰트로 HTML·PDF를 생성합니다.

```bash
python tools/build_reports.py AST_ID --revision REV001
```

각 개정본은 영문·국문 Markdown, HTML, PDF의 6개 출력을 보존하며 이전 개정본을 덮어쓰지 않습니다. 과학적 적절성, 양 언어의 의미 대응, 실제 렌더링 결과는 별도로 검토해야 합니다. 자세한 설정은 [보고서 안내](docs/REPORTING.md)를 참고하세요.

## 기존 프로젝트 업데이트

새 버전의 Framework를 받은 뒤 새 저장소에서 다음 명령을 실행합니다.

```bash
python3 tools/update_project.py /absolute/path/to/my_research
python3 tools/update_project.py /absolute/path/to/my_research --apply
```

첫 명령은 **파일을 수정하지 않고 변경 예정 사항을 보여 줍니다**. 이전 템플릿, 로컬 수정, 새 템플릿을 비교하여 안전한 변경만 적용합니다. 해결되지 않은 충돌이 있으면 전체 적용이 중단됩니다. 수정 대상의 백업은 프로젝트의 `.framework/backups/`에 남습니다. 연구 보고서, 계획서, 데이터, 독립 코드 저장소, 프로젝트 설정은 자동 업데이트 대상이 아닙니다. [파일 소유권 및 업데이트 안내](docs/OWNERSHIP_AND_UPDATES.md)를 참고하세요.

## 저장소 구성 및 추가 문서

```text
template/       실제 연구 프로젝트 템플릿과 운영 지침, 스크립트
tools/          프로젝트 생성, 업데이트, 릴리스 도구
newproj         간편한 새 프로젝트 생성 명령
docs/           설계 철학, 과학적 명세, 사용 및 구현 문서
tests/          합성 프로젝트와 보고서 테스트
```

- [설계 철학 (한국어)](docs/PHILOSOPHY.ko.md): 이 Framework가 왜 이런 형태인지
- [Design Philosophy (English)](docs/PHILOSOPHY.md): 영문 설계 철학
- [과학적 설계 명세 (한국어)](docs/RESEARCH_PROGRAM_FRAMEWORK_v1.1_ko.md): Narrative, Workstream, AST 등의 상세 정의
- [아키텍처](docs/ARCHITECTURE.md) 및 [릴리스 안내](docs/RELEASE_NOTES.md): 실제 구현과 버전 설명

이 프레임워크는 숨겨진 런타임 ZIP이나 특정 AI 채팅의 기억에 의존하지 않고 프로젝트를 이해하고 이어갈 수 있도록 설계되었습니다.
