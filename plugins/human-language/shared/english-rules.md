# 영어 특화 탈-AI 작문 규칙 (English Rules)

영문 텍스트 생성 및 검수 시 적용되는 세부 규칙입니다.

---

## 1. AI 과대표집 어휘 (Banned Words) 정화

다음과 같은 RLHF 과대표집 어휘는 기계적인 느낌을 주므로 일상적이고 구체적인 단어로 대체합니다. 단어 자체는 정상 어휘이므로, 한 문단에 여러 개가 몰려 있거나 구체적 내용 없이 수식으로만 쓰일 때 교정하고 하나만 자연스럽게 쓰인 경우는 그대로 둡니다:
* **지양 어휘**: *delve, tapestry, pivotal, underscore, testament, landscape, holistic, vibrant, beacon, foster, nuanced, paramount, comprehensive, seamless, revolutionize, realm*
* **교정 방향**:
  - `delve into` ➔ `examine`, `look at`, `explore`
  - `testament to` ➔ `shows that`, `proves`
  - `pivotal role` ➔ `key factor`, `important part`
  - `tapestry of` ➔ `mix of`, `collection of`

---

## 2. 정형화된 구문 구조 해체

* **Parallel Negation 해체**:
  - `It is not just about X, but also about Y` ➔ 직결: `It covers both X and Y.` 또는 Y만 진술.
* **Tricolon (Rule of Threes) 해체**:
  - 형용사나 불릿 항목 3개를 기계적으로 병렬 배치하는 패턴을 깨십시오. 내용상 실제로 셋이면 그대로 쓰고, 개수를 채우려 덧붙인 항목만 걷어내거나 사실 중심 단문으로 분리.
* **Rhetorical Q&A 금지**:
  - `Why does this matter? Because...` ➔ 자문자답을 지양하고 본론부터 직접 서술.
* **Em Dash(`—`) 남발 제한**:
  - 한 문단에 여러 개의 Em dash를 장식용으로 삽입하지 말고, 마침표로 문장을 끊거나 쉼표를 사용.

---

## 3. 톤 및 명료성

* **능동태 우선 (Active Voice)**:
  - 무생물 주어 수동태(`The results were analyzed by...`) ➔ 능동태(`We analyzed...`)로 변경.
* **명확한 기술 (Direct & Concise)**:
  - 장황한 완곡어법(*"It could potentially be argued that..."*)을 걷어내고 직접 서술.
* **호흡 변주 (Burstiness)**:
  - 모든 문장이 20~25단어로 획일화되지 않도록, 아주 짧은 단문(5~8단어)과 복문을 교차 배치.
