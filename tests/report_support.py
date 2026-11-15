"""Bilingual synthetic evidence fixture; no real observations or research claims."""

import json

from build_reports import SECTIONS


UNIT_ID = 'A001-S01-T01'
EN = [
    'This software demonstration asks whether synthetic values survive paired reporting. No biological observations were collected.',
    'The synthetic Aim is to test evidence communication. The bounded question is whether constructed values retain their definitions in both languages.',
    'Use a deterministic descriptive demonstration, with no intervention, sampling claim or causal inference.',
    r'''Construct four values, 1, 2, 3 and 4, in arbitrary units (a.u.). Each value is a constructed observation; there are no biological or technical replicates. All four values are included. There is no assignment, missingness, exclusion, filtering, preprocessing, normalization or transformation. No experiment, instrument acquisition or controlled participant data is involved.

Calculate the arithmetic mean $\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i$, where $x_i$ is constructed value $i$, $n=4$ is the number of constructed values, and $\bar{x}$ has units a.u. The result is 2.5 a.u. No uncertainty estimate, resampling, significance test, multiplicity adjustment or inferential threshold is used because this is a deterministic software fixture. No control group or causal comparison is claimed. Verify the arithmetic against the primary table; this consistency check is not an independent scientific replication.''',
    'The effective input is the explicitly constructed ordered list, with n=4. There are no tunable parameters, random seeds, protocols, batches or model fitting. Acceptance requires exact table values and matching definitions.',
    'The fixture was constructed locally for software acceptance. The arithmetic was checked directly. No external execution or historical reproduction is claimed.',
    '| Constructed observation | Value (a.u.) |\n|:--|--:|\n| First | 1 |\n| Second | 2 |\n| Third | 3 |\n| Fourth | 4 |\n\nThe table is the primary evidence. It uses the original constructed scale, with no exclusions or uncertainty bars.',
    'All four constructed values are present; their arithmetic mean is 2.5 a.u. These are fixture values rather than biological measurements.',
    'The deterministic values are consistent with the descriptive calculation. This validates a software path and supports no biological, predictive or causal claim.',
    'A synthetic fixture cannot establish scientific validity, translation quality for arbitrary manuscripts, or performance on every journal layout. No follow-up experiment is authorized.',
    'The primary record is this synthetic fixture and its table. Source defaults, producing revision and past execution history are not inferred. No restricted data, remote source, or unobserved transfer is involved.'
]
KO = [
    '이 소프트웨어 시연은 합성 값이 두 언어의 보고서에서 보존되는지 확인한다. 생물학적 관측은 수집하지 않았다.',
    '합성 Aim은 증거 전달 경로를 시험하는 것이다. 범위가 제한된 질문은 구성한 값의 정의가 두 언어에서 유지되는지 여부이다.',
    '결정론적인 기술적 시연을 사용하며 개입·표본 추출·인과 추론을 주장하지 않는다.',
    r'''임의 단위(a.u.)의 값 1, 2, 3, 4를 구성한다. 각 값은 구성된 관측이며 생물학적·기술적 반복은 없다. 네 값을 모두 포함한다. 배정·결측·제외·필터·전처리·정규화·변환은 없다. 실험, 기기 획득 또는 통제된 참여자 자료는 사용하지 않는다.

산술평균 $\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i$를 계산한다. $x_i$는 구성한 관측 $i$의 값이고, $n=4$는 구성한 값의 수이며 $\bar{x}$의 단위는 a.u.이다. 결과는 2.5 a.u.이다. 결정론적인 소프트웨어 fixture이므로 불확실성 추정·재표본화·유의성 검정·다중비교 보정·추론 threshold를 사용하지 않는다. 대조군이나 인과 비교를 주장하지 않는다. 주요 표와 산술 계산의 일관성을 검사하며 이를 독립적인 과학적 재현으로 표시하지 않는다.''',
    '실제 입력은 명시적으로 구성한 순서가 있는 목록이며 n=4이다. 조정 파라미터·난수 seed·프로토콜·배치·모델 적합은 없다. 표의 값과 정의가 정확히 일치해야 한다.',
    '이 fixture는 소프트웨어 수용 검사를 위해 로컬에서 구성했다. 산술 계산을 직접 확인했다. 외부 실행이나 과거 실행의 재현을 주장하지 않는다.',
    '| 구성한 관측 | 값 (a.u.) |\n|:--|--:|\n| 첫째 | 1 |\n| 둘째 | 2 |\n| 셋째 | 3 |\n| 넷째 | 4 |\n\n표가 주요 증거이다. 구성한 원래 척도를 사용하며 제외나 불확실성 막대는 없다.',
    '구성한 값 네 개가 모두 존재하며 산술평균은 2.5 a.u.이다. 생물학적 측정값이 아닌 fixture 값이다.',
    '결정론적인 값은 기술적 계산과 일치한다. 이는 소프트웨어 경로의 검사이며 생물학적·예측적·인과적 주장을 뒷받침하지 않는다.',
    '합성 fixture로 과학적 타당성, 임의 논문의 번역 품질 또는 모든 학술지 조판 성능을 확정할 수 없다. 후속 실험은 승인하지 않는다.',
    '일차 기록은 이 합성 fixture와 표이다. 소스 기본값, 결과 생성 revision 또는 과거 실행 이력은 추정하지 않는다. 제한된 자료·원격 출처·확인하지 않은 전송은 없다.'
]


def sources(project, revision='REV001', methods_repeat=1):
    root = project / 'reports' / UNIT_ID
    for lang, bodies in [('en', EN), ('ko', KO)]:
        text = f'# {UNIT_ID}: Synthetic evidence\n\n**Unit ID:** {UNIT_ID}\n**Status:** COMPLETED\n**Outcome:** NOT_EVALUATED\n**Report revision:** {revision}\n\n'
        for index, (key, body) in enumerate(zip(SECTIONS, bodies)):
            label = key if lang == 'en' else dict(zip(SECTIONS, ['과학적 동기','Aim과 Tactic 질문','전략','Tactic과 방법','명세','수행과 검증','그림 또는 주요 증거','결과','분석과 해석','한계와 후속 질문','재현성과 산출물 참조']))[key]
            text += f'<!-- section: {key} -->\n## {index+1}. {label}\n\n' + ('\n\n'.join([body] * methods_repeat) if key == 'methods' else body) + '\n\n'
        target = root / lang / 'report.md'; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
    metadata = {'unit_id': UNIT_ID, 'status': 'COMPLETED', 'outcome': 'NOT_EVALUATED',
        'outcome_reason': 'A deterministic software demonstration, with no scientific hypothesis evaluated.',
        'revision': revision, 'figures': [], 'provenance': [],
        'review': {'methods': True, 'bilingual': True, 'visual': False, 'references': ['Synthetic fixture source reviewed for software acceptance.']}}
    (root / 'report.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    return root


def figure(project):
    """Create a synthetic plot, never a measurement-image transformation."""
    import os
    from pathlib import Path
    import tempfile
    os.environ.setdefault('MPLCONFIGDIR', tempfile.mkdtemp(prefix='rpf-figure-cache-'))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib import font_manager
    if os.environ.get('RPF_ARIAL'):
        font_manager.fontManager.addfont(os.environ['RPF_ARIAL'])
    font_manager.findfont(font_manager.FontProperties(family='Arial'), fallback_to_default=False)
    with plt.rc_context({'font.family': 'Arial', 'font.size': 6, 'text.color': '#000000',
                         'axes.labelcolor': '#000000', 'xtick.color': '#000000', 'ytick.color': '#000000',
                         'svg.fonttype': 'none', 'pdf.fonttype': 42}):
        fig, ax = plt.subplots(figsize=(85/25.4, 55/25.4), layout='constrained')
        ax.scatter([1,2,3,4], [1,2,3,4], s=8, color='#175d9c')
        ax.set(xlabel='Constructed observation index', ylabel='Constructed value (a.u.)', xticks=[1,2,3,4])
        root = project / 'analyses' / UNIT_ID / 'figures'; root.mkdir(parents=True, exist_ok=True)
        for suffix in ('png','pdf','svg'): fig.savefig(root / ('synthetic.'+suffix), dpi=600)
        plt.close(fig)
    report = project / 'reports' / UNIT_ID
    for lang in ('en','ko'):
        path = report / lang / 'report.md'; text = path.read_text()
        caption = ('Constructed observation index on the x axis; constructed value in a.u. on the y axis. Both axes use linear scales. Blue points show the four original constructed values; there are no connecting lines, transformations, exclusions, thresholds or uncertainty bars.'
                   if lang == 'en' else 'x축은 구성한 관측의 순서이고 y축은 임의 단위(a.u.)의 구성한 값이다. 두 축은 선형 척도이다. 파란 점은 구성한 원래 값 네 개를 나타낸다. 연결선·변환·제외·threshold·불확실성 막대는 없다.')
        text = text.replace('<!-- section: results -->', '![Synthetic constructed values](../../../analyses/'+UNIT_ID+'/figures/synthetic.png)\n\n'+caption+'\n\n<!-- section: results -->')
        path.write_text(text)
    path = report / 'report.json'; metadata = json.loads(path.read_text())
    metadata['figures'] = [{'path': 'analyses/'+UNIT_ID+'/figures/synthetic.'+suffix, 'width_mm':85,
        'kind':'plot','font_family':'Arial','text_size_pt':6,'exception':None,'raster_embedded':False}
        for suffix in ('png','pdf','svg')]
    path.write_text(json.dumps(metadata, ensure_ascii=False,indent=2)+'\n')
