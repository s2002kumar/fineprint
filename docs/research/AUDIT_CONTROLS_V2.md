# Audit controls v2: independent product-level negative controls

**Status: frozen 2026-10-22T09:15:54Z** (seed `fineprint-audit-controls-v2-2026-10-22`, graph build 8; machine-readable `audit_controls_v2.json`, SHA-256 `8afc2bed621814c283523fe2222f40362ec9e1f06d0786d091c7233d1ffd0f3b`). The original worksheet sample (`docs/HUMAN_AUDIT_WORKSHEET.md`, seed `fineprint-human-audit-2026-10-20`) is unchanged; this file adds to it.

## Why the original C19/C20 are weak

C19 (LABEL by Rocky Mount for Precedex 0409-4596) and C20 (PACK by Rocky Mount for Vitamin K1 0409-9158) do test that a PACK or LABEL element is not recorded as MANUFACTURE. But both labels also contain a separate MANUFACTURE assertion by the same DUNS for the same product, so at product level the graph's answer ('Rocky Mount makes it') is correct either way. They cannot catch a classifier that conflates operations. They are retained as operation-level checks:

- **C19**: the LABEL edge 113224 has is_manufacture = false — observed is_manufacture = `False` (ok). Weak because set 92b7ddaa… also asserts MANUFACTURE (C43360) by DUNS 093132819 for 0409-4596 (edge 113220).
- **C20**: the PACK edge 121363 has is_manufacture = false — observed is_manufacture = `False` (ok). Weak because set e8808230… also asserts MANUFACTURE by DUNS 093132819 for 0409-9158 (edge 121361).

## New controls

Each control names a product whose label contains a specific non-manufacturing or non-attributable assertion, and states what the graph must say. A person checks the label (FDA XML by document ID, fixed bytes; or DailyMed) and then the explorer or `fp.py product <ndc>`. 'Premise' was re-checked in the raw XML by an independent walk; 'expectation' was checked against the graph tables.

| Id | Type | Product | Label | Premise holds | Expectation holds |
|---|---|---|---|---|---|
| N01 | N1 PACK without MANUFACTURE | `71863-109` AlkindiSprinkle | set `26c13a5f…` v20 | yes | yes |
| N02 | N1 PACK without MANUFACTURE | `0069-3051` ZITHROMAX | set `b749df83…` v42 | yes | yes |
| N03 | N1 PACK without MANUFACTURE | `62135-826` Albuterol Sulfate | set `4e48ccbe…` v3 | yes | yes |
| N04 | N2 LABEL without MANUFACTURE | `51754-1210` Bloxiverz | set `d2f55643…` v18 | yes | yes |
| N05 | N2 LABEL without MANUFACTURE | `25208-901` AGGRASTAT | set `e850111f…` v3 | yes | yes |
| N06 | N2 LABEL without MANUFACTURE | `0069-0296` Talzenna | set `f2423edd…` v19 | yes | yes |
| N07 | N3 ANALYSIS without MANUFACTURE | `0409-4520` Heparin Sodium and Dextrose | set `eede8a0c…` v35 | yes | yes |
| N08 | N3 ANALYSIS without MANUFACTURE | `14789-127` Phenobarbital Sodium | set `472da201…` v6 | yes | yes |
| N09 | N3 ANALYSIS without MANUFACTURE | `60687-917` Lactulose | set `8b79d0d6…` v1 | yes | yes |
| N10 | N4 API MANUFACTURE only | `61958-1501` Sovaldi | set `80beab2c…` v16 | yes | yes |
| N11 | N4 API MANUFACTURE only | `63304-694` Minocycline hydrochloride | set `61f1d07a…` v4 | yes | yes |
| N12 | N4 API MANUFACTURE only | `0013-2626` GENOTROPIN | set `ffebf88b…` v37 | yes | yes |
| N13 | N5 API site versus finished-dose site | `58468-0220` Cerdelga | set `819f828a…` v13 | yes | yes |
| N14 | N5 API site versus finished-dose site | `59762-0935` Voriconazole | set `b8de04a0…` v62 | yes | yes |
| N15 | N5 API site versus finished-dose site | `0024-5840` ZALTRAP | set `f6725df6…` v28 | yes | yes |
| N16 | N6 MANUFACTURE with no product scope (single-product label) | `22100-007` Healing Waters Sweet Pea Lily Hand Sanitizer | set `ce67712f…` v1 | yes | yes |
| N17 | N6 MANUFACTURE with no product scope (single-product label) | `62646-798` Anticoagulant Sodium Citrate | set `3a8dfcfa…` v4 | yes | yes |
| N18 | N6 MANUFACTURE with no product scope (single-product label) | `58177-293` metoprolol succinate extended-release | set `a8374722…` v3 | yes | yes |
| N19 | N7 MANUFACTURE by an unresolved DUNS | `43598-204` amoxicillin and clavulanate potassium | set `58a20183…` v7 | yes | yes |
| N20 | N7 MANUFACTURE by an unresolved DUNS | `72934-8170` SALICYLIC ACID 2% /SODIUM SULFACETAMIDE MONOHYDRATE 8% | set `87395273…` v1 | yes | yes |
| N21 | N7 MANUFACTURE by an unresolved DUNS | `52565-096` ZANTAC | set `95dc4515…` v4 | yes | yes |
| N22 | N8 MANUFACTURE by a stale-registration DUNS | `60615-0001` Oxygen | set `448541b9…` v8 | yes | yes |
| N23 | N8 MANUFACTURE by a stale-registration DUNS | `84778-114` Salkalli | set `4301f19f…` v1 | yes | yes |

### N1 · PACK without MANUFACTURE

- **Premise:** The product's only operations include PACK (C84731) by a DUNS; no establishment asserts MANUFACTURE (C43360) for it.
- **Expectation:** No MANUFACTURE edge for the product; manufacturing_status NO_MANUFACTURE_EVIDENCE; the PACK edge has is_manufacture = false.
- **What it catches:** A reader who treats the packer as the maker would wrongly assign a manufacturing site.
- Eligible: 173 products in 104 sets.

#### N01 · `71863-109` AlkindiSprinkle
- Label set `26c13a5f-7119-4c6a-bf10-fda4e07d7682` version 20: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/4ffdccff-95d3-7c88-e063-6394a90a1c9f/4ffdccff-95d3-7c88-e063-6394a90a1c9f.xml) (expected XML SHA-256 `bb47dc77835ff24713ba30a57690d6fc9bd405c0ccc8d546d7eafcd47b5344b0`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=26c13a5f-7119-4c6a-bf10-fda4e07d7682). Products in label: 4.
- Raw XML operations naming this product: [('C84731', 'pack', '361961142')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: PACK 361961142 DIRECT [104749].
- Premise holds: **yes**; expectation holds: **yes**.

#### N02 · `0069-3051` ZITHROMAX
- Label set `b749df83-49b0-433e-8a62-589a048dd716` version 42: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/a7e796ea-105f-4068-8d6f-3d9c9802e13c/a7e796ea-105f-4068-8d6f-3d9c9802e13c.xml) (expected XML SHA-256 `60c25ed65658e0603dc3b8b2ab45fa7fd7bdd11c9f42476fa5b5683c05452e79`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b749df83-49b0-433e-8a62-589a048dd716). Products in label: 2.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '069777290'), ('C25391', 'ANALYSIS', '829084552'), ('C25391', 'ANALYSIS', '936889401'), ('C25391', 'ANALYSIS', '943955690'), ('C25391', 'ANALYSIS', '985052076'), ('C82401', 'API MANUFACTURE', '936889401'), ('C82401', 'API MANUFACTURE', '985052076'), ('C84731', 'PACK', '829084552')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: ANALYSIS 985052076 DIRECT [77388]; API MANUFACTURE 985052076 DIRECT [77390]; ANALYSIS 943955690 TENTATIVE ['identity:STALE_REGISTERED'] [77392]; API MANUFACTURE 936889401 DIRECT [77395]; ANALYSIS 936889401 DIRECT [77397]; ANALYSIS 069777290 DIRECT [77399]; PACK 829084552 DIRECT [77401]; ANALYSIS 829084552 DIRECT [77403].
- Premise holds: **yes**; expectation holds: **yes**.

#### N03 · `62135-826` Albuterol Sulfate
- Label set `4e48ccbe-3ec0-4bf2-be28-83eb9baa63d6` version 3: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/11e59625-431b-e530-e063-6294a90a0596/11e59625-431b-e530-e063-6294a90a0596.xml) (expected XML SHA-256 `ae8508473114c50f5dbca833d98b1dc906d9d9c2bb556215240623430fa0c7c6`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=4e48ccbe-3ec0-4bf2-be28-83eb9baa63d6). Products in label: 2.
- Raw XML operations naming this product: [('C84731', 'pack', '118673447')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: PACK 118673447 DIRECT [41984].
- Premise holds: **yes**; expectation holds: **yes**.

### N2 · LABEL without MANUFACTURE

- **Premise:** The product's only operations include LABEL (C84732) by a DUNS; no MANUFACTURE for it.
- **Expectation:** No MANUFACTURE edge; status NO_MANUFACTURE_EVIDENCE; LABEL edge is_manufacture = false.
- **What it catches:** Treating the labeling site as the maker.
- Eligible: 156 products in 95 sets.

#### N04 · `51754-1210` Bloxiverz
- Label set `d2f55643-2b0d-4ef9-a9d8-b7138b314372` version 18: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/f9ddedaa-a4a1-4fa2-8a3e-a3bb3abdde47/f9ddedaa-a4a1-4fa2-8a3e-a3bb3abdde47.xml) (expected XML SHA-256 `96facf960e6a0afac006badd99fe5b12fcc703e85f4129f068cd349f15b36690`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=d2f55643-2b0d-4ef9-a9d8-b7138b314372). Products in label: 3.
- Raw XML operations naming this product: [('C84732', 'LABEL', '831274399')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: LABEL 831274399 DIRECT [40583].
- Premise holds: **yes**; expectation holds: **yes**.

#### N05 · `25208-901` AGGRASTAT
- Label set `e850111f-e713-41a2-9c65-21c517cf5511` version 3: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/d7b2e8c6-afd1-4e94-b780-ed2fc439e3f3/d7b2e8c6-afd1-4e94-b780-ed2fc439e3f3.xml) (expected XML SHA-256 `8f88beacce6980a863a718fe44e51115369b868a466029eb7cf035dda2b78bd8`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e850111f-e713-41a2-9c65-21c517cf5511). Products in label: 2.
- Raw XML operations naming this product: [('C84731', 'pack', '463719725'), ('C84732', 'label', '463719725')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: LABEL 463719725 DIRECT [59344]; LABEL 463719725 DIRECT [59346]; PACK 463719725 DIRECT [59348].
- Premise holds: **yes**; expectation holds: **yes**.

#### N06 · `0069-0296` Talzenna
- Label set `f2423edd-6d24-495c-aec1-c2f457f08d9a` version 19: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/e189da1b-d503-48a4-aba3-4f93a3fab2d3/e189da1b-d503-48a4-aba3-4f93a3fab2d3.xml) (expected XML SHA-256 `c6076b1cacc1bb42255bddfd8b335929adcc95c7ffde89b4d8d0050d1e236ac3`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=f2423edd-6d24-495c-aec1-c2f457f08d9a). Products in label: 6.
- Raw XML operations naming this product: [('C84731', 'PACK', '829084552'), ('C84732', 'LABEL', '618054084'), ('C84732', 'LABEL', '829084552')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: PACK 829084552 DIRECT [84969]; LABEL 829084552 DIRECT [84975]; LABEL 618054084 DIRECT [84981].
- Premise holds: **yes**; expectation holds: **yes**.

### N3 · ANALYSIS without MANUFACTURE

- **Premise:** The product's only operations include ANALYSIS (C25391) by a DUNS; no MANUFACTURE for it.
- **Expectation:** No MANUFACTURE edge; status NO_MANUFACTURE_EVIDENCE; ANALYSIS edge is_manufacture = false.
- **What it catches:** Treating a testing laboratory as the maker.
- Eligible: 318 products in 169 sets.

#### N07 · `0409-4520` Heparin Sodium and Dextrose
- Label set `eede8a0c-5ae6-4166-84b3-12081405f08e` version 35: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/b2a0ec6b-eee0-46b9-9e8a-ae2442e30771/b2a0ec6b-eee0-46b9-9e8a-ae2442e30771.xml) (expected XML SHA-256 `448a8a91ee0425888e86118a0875bb05b77f6698180f8b5f7bfe1df5a618a53a`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=eede8a0c-5ae6-4166-84b3-12081405f08e). Products in label: 3.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '030606222')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: ANALYSIS 030606222 DIRECT [108987].
- Premise holds: **yes**; expectation holds: **yes**.

#### N08 · `14789-127` Phenobarbital Sodium
- Label set `472da201-698e-4d2b-8c53-595461d85bb6` version 6: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/45c7f956-27bd-dc6d-e063-6394a90a6181/45c7f956-27bd-dc6d-e063-6394a90a6181.xml) (expected XML SHA-256 `d884c8e896a34269cdda4bb435b2f7d9cd225abe69cacea3c9aacf73279934db`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=472da201-698e-4d2b-8c53-595461d85bb6). Products in label: 2.
- Raw XML operations naming this product: [('C25391', 'analysis', '620714787')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: ANALYSIS 620714787 DIRECT [83871].
- Premise holds: **yes**; expectation holds: **yes**.

#### N09 · `60687-917` Lactulose
- Label set `8b79d0d6-b9e3-436e-bab7-01451b6f45cd` version 1: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/5942b819-43c4-53a4-e063-6394a90af393/5942b819-43c4-53a4-e063-6394a90af393.xml) (expected XML SHA-256 `1c78c2c27d23ddea71e142bcf491de7b7efc56e79790b2735a50eaf63a134f17`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8b79d0d6-b9e3-436e-bab7-01451b6f45cd). Products in label: 1.
- Raw XML operations naming this product: [('C25391', 'analysis', '929561009'), ('C73606', 'repack', '929561009')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: REPACK 929561009 DIRECT [122380]; ANALYSIS 929561009 DIRECT [122381].
- Premise holds: **yes**; expectation holds: **yes**.

### N4 · API MANUFACTURE only

- **Premise:** An establishment asserts API MANUFACTURE (C82401) for the product; nobody asserts finished-dose MANUFACTURE (C43360).
- **Expectation:** No MANUFACTURE edge; status NO_MANUFACTURE_EVIDENCE; the C82401 edge has is_manufacture = false and operation_name 'API MANUFACTURE'.
- **What it catches:** Collapsing the API (drug substance) maker into the finished-product maker.
- Eligible: 249 products in 115 sets.

#### N10 · `61958-1501` Sovaldi
- Label set `80beab2c-396e-4a37-a4dc-40fdb62859cf` version 16: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/74c52ec6-8358-4e63-b299-64ec1ff7f434/74c52ec6-8358-4e63-b299-64ec1ff7f434.xml) (expected XML SHA-256 `736662c1f8f1042486a8a6773dd265c50f6dd98550aec47a649a7621e3943975`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=80beab2c-396e-4a37-a4dc-40fdb62859cf). Products in label: 4.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '431189117'), ('C82401', 'API MANUFACTURE', '431189117')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: API MANUFACTURE 431189117 DIRECT [60692]; ANALYSIS 431189117 DIRECT [60696].
- Premise holds: **yes**; expectation holds: **yes**.

#### N11 · `63304-694` Minocycline hydrochloride
- Label set `61f1d07a-f5e9-45b5-8806-b31a441bc592` version 4: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/1ffca7b6-8f19-4a26-9578-cbdd72296068/1ffca7b6-8f19-4a26-9578-cbdd72296068.xml) (expected XML SHA-256 `ba09d02a2b0b9d3c46432b60868149ee30b19d8484ffa42cc8e87fddee236fbb`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=61f1d07a-f5e9-45b5-8806-b31a441bc592). Products in label: 3.
- Raw XML operations naming this product: [('C101510', 'FDF MANUFACTURE', '051565745'), ('C82401', 'api manufacture', '430253557'), ('C84731', 'pack', '051565745')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: FDF MANUFACTURE 051565745 DIRECT [9276]; PACK 051565745 DIRECT [9279]; API MANUFACTURE 430253557 UNKNOWN ['identity:NOT_FOUND'] [9282].
- Premise holds: **yes**; expectation holds: **yes**.

#### N12 · `0013-2626` GENOTROPIN
- Label set `ffebf88b-d257-4542-9808-74d9b7167765` version 37: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/5aa3307a-c0bc-43c0-8177-3bb1cad66d7a/5aa3307a-c0bc-43c0-8177-3bb1cad66d7a.xml) (expected XML SHA-256 `b60db867f5f32e7fa5aa416940444929928e58795e4e5bd9b1cb193adc15d00b`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ffebf88b-d257-4542-9808-74d9b7167765). Products in label: 12.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '354433591'), ('C82401', 'API MANUFACTURE', '354433591')]; MANUFACTURE DUNS for it: none.
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (OTHER_OPERATIONS_ONLY); edges: API MANUFACTURE 354433591 DIRECT [120545]; ANALYSIS 354433591 DIRECT [120557].
- Premise holds: **yes**; expectation holds: **yes**.

### N5 · API site versus finished-dose site

- **Premise:** DUNS X asserts only API MANUFACTURE for the product while a different DUNS Y asserts MANUFACTURE.
- **Expectation:** X is not among the product's MANUFACTURE DUNS; Y is. The API edge is_manufacture = false.
- **What it catches:** Counting the API supplier as a second finished-dose site.
- Eligible: 1512 products in 663 sets.

#### N13 · `58468-0220` Cerdelga
- Label set `819f828a-b888-4e46-83fc-94d774a28a83` version 13: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/e71b0b39-5a29-4e38-8500-55b6d1f48543/e71b0b39-5a29-4e38-8500-55b6d1f48543.xml) (expected XML SHA-256 `da1fcbe655148404470d8a5ec8621d2ab1a5a68efb584f4ce2081e0ad161e1e4`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=819f828a-b888-4e46-83fc-94d774a28a83). Products in label: 1.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '481829653'), ('C25391', 'ANALYSIS', '571879985'), ('C25391', 'ANALYSIS', '763683216'), ('C25391', 'ANALYSIS', '985127419'), ('C43360', 'MANUFACTURE', '571879985'), ('C43360', 'MANUFACTURE', '763683216'), ('C43360', 'MANUFACTURE', '985127419'), ('C82401', 'API MANUFACTURE', '481829653'), ('C84731', 'PACK', '571879985'), ('C84731', 'PACK', '763683216'), ('C84731', 'PACK', '985127419'), ('C84732', 'LABEL', '571879985'), ('C84732', 'LABEL', '763683216'), ('C84732', 'LABEL', '985127419')]; MANUFACTURE DUNS for it: ['571879985', '763683216', '985127419'].
- Graph: manufacturing_status **DIRECT** (EXPLICIT_MANUFACTURE); edges: API MANUFACTURE 481829653 DIRECT [42521]; ANALYSIS 481829653 DIRECT [42522]; ANALYSIS 985127419 DIRECT [42523]; MANUFACTURE 985127419 DIRECT [42524]; PACK 985127419 DIRECT [42525]; LABEL 985127419 DIRECT [42526]; ANALYSIS 571879985 DIRECT [42527]; MANUFACTURE 571879985 DIRECT [42528]; PACK 571879985 DIRECT [42529]; LABEL 571879985 DIRECT [42530]; ANALYSIS 763683216 DIRECT [42531]; MANUFACTURE 763683216 DIRECT [42532]; PACK 763683216 DIRECT [42533]; LABEL 763683216 DIRECT [42534].
- Premise holds: **yes**; expectation holds: **yes**.

#### N14 · `59762-0935` Voriconazole
- Label set `b8de04a0-238d-4e0b-b0d9-7f7878b149d4` version 62: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/7131a7cd-db5a-4ac2-9a84-09059d62669e/7131a7cd-db5a-4ac2-9a84-09059d62669e.xml) (expected XML SHA-256 `7eeccd41505a122ede898e0171f6ad086c7865ade6fc52555fbbb2e4a4ceb0f1`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b8de04a0-238d-4e0b-b0d9-7f7878b149d4). Products in label: 1.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '458521908'), ('C25391', 'ANALYSIS', '985052076'), ('C43360', 'MANUFACTURE', '458521908'), ('C82401', 'API MANUFACTURE', '985052076'), ('C82401', 'API MANUFACTURE', '986030667'), ('C84731', 'PACK', '458521908'), ('C84732', 'LABEL', '458521908')]; MANUFACTURE DUNS for it: ['458521908'].
- Graph: manufacturing_status **DIRECT** (EXPLICIT_MANUFACTURE); edges: ANALYSIS 458521908 DIRECT [110239]; MANUFACTURE 458521908 DIRECT [110240]; PACK 458521908 DIRECT [110241]; LABEL 458521908 DIRECT [110242]; API MANUFACTURE 985052076 DIRECT [110243]; ANALYSIS 985052076 DIRECT [110244]; API MANUFACTURE 986030667 DIRECT [110245].
- Premise holds: **yes**; expectation holds: **yes**.

#### N15 · `0024-5840` ZALTRAP
- Label set `f6725df6-50ee-4b0a-b900-d02ba634395d` version 28: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/14431dcb-cda7-4ae4-aa2b-6480d6ac459f/14431dcb-cda7-4ae4-aa2b-6480d6ac459f.xml) (expected XML SHA-256 `371a316b5b2b4986ed1308c81c88cc803a1dcf1101069addf81d24e12674b3d0`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=f6725df6-50ee-4b0a-b900-d02ba634395d). Products in label: 2.
- Raw XML operations naming this product: [('C25391', 'ANALYSIS', '313218430'), ('C25391', 'ANALYSIS', '945589711'), ('C43360', 'MANUFACTURE', '313218430'), ('C82401', 'API MANUFACTURE', '945589711'), ('C84731', 'PACK', '313218430'), ('C84732', 'LABEL', '313218430')]; MANUFACTURE DUNS for it: ['313218430'].
- Graph: manufacturing_status **DIRECT** (EXPLICIT_MANUFACTURE); edges: ANALYSIS 945589711 DIRECT [93700]; API MANUFACTURE 945589711 DIRECT [93702]; ANALYSIS 313218430 DIRECT [93704]; LABEL 313218430 DIRECT [93706]; MANUFACTURE 313218430 DIRECT [93708]; PACK 313218430 DIRECT [93710].
- Premise holds: **yes**; expectation holds: **yes**.

### N6 · MANUFACTURE with no product scope (single-product label)

- **Premise:** The label has exactly one product, and an establishment asserts MANUFACTURE without naming any product code.
- **Expectation:** The product's manufacturing_status is NO_MANUFACTURE_EVIDENCE (ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT); the MANUFACTURE edge is UNKNOWN with reason scope:no_product_scope and product_pk NULL.
- **What it catches:** The tempting inference 'there is only one product, so the unscoped MANUFACTURE must be for it'. The rule does not make it; this control pins that.
- Eligible: 680 products in 680 sets.

#### N16 · `22100-007` Healing Waters Sweet Pea Lily Hand Sanitizer
- Label set `ce67712f-3bfb-4317-bd10-316f86122eda` version 1: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/9e20bee7-0480-40a3-b6b9-190360e5562f/9e20bee7-0480-40a3-b6b9-190360e5562f.xml) (expected XML SHA-256 `3eec13ce70b3a4be1b2f34af31d016bea10305dac774711364dfc7135b71e059`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ce67712f-3bfb-4317-bd10-316f86122eda). Products in label: 1.
- Raw XML operations naming this product: none; MANUFACTURE DUNS for it: none; unscoped MANUFACTURE DUNS in label: ['547230008'].
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT); edges: MANUFACTURE 547230008 UNKNOWN ['scope:no_product_scope'] [303].
- Premise holds: **yes**; expectation holds: **yes**.

#### N17 · `62646-798` Anticoagulant Sodium Citrate
- Label set `3a8dfcfa-e034-40ca-a71f-05099015f87d` version 4: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/a083fb8e-3012-4d12-94d3-949a3188aba3/a083fb8e-3012-4d12-94d3-949a3188aba3.xml) (expected XML SHA-256 `9f54d8bf3959923277f417f7e506971be009fe2b9d83bd5e7d4901a7c4589e94`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3a8dfcfa-e034-40ca-a71f-05099015f87d). Products in label: 1.
- Raw XML operations naming this product: none; MANUFACTURE DUNS for it: none; unscoped MANUFACTURE DUNS in label: ['928224765'].
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT); edges: MANUFACTURE 928224765 UNKNOWN ['scope:no_product_scope'] [6097]; RELABEL 928224765 UNKNOWN ['scope:no_product_scope'] [6098]; REPACK 928224765 UNKNOWN ['scope:no_product_scope'] [6099].
- Premise holds: **yes**; expectation holds: **yes**.

#### N18 · `58177-293` metoprolol succinate extended-release
- Label set `a8374722-d2b5-4eb3-bbcd-6ddc52e763ba` version 3: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/68235c8d-a5fa-49c8-aebd-214e6c47e410/68235c8d-a5fa-49c8-aebd-214e6c47e410.xml) (expected XML SHA-256 `581f178b9eaf8bb548dada95606d926b2790889f571a4960637593c515dd9ae7`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a8374722-d2b5-4eb3-bbcd-6ddc52e763ba). Products in label: 1.
- Raw XML operations naming this product: none; MANUFACTURE DUNS for it: none; unscoped MANUFACTURE DUNS in label: ['152053658', '161097225'].
- Graph: manufacturing_status **NO_MANUFACTURE_EVIDENCE** (ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT); edges: MANUFACTURE 161097225 UNKNOWN ['scope:no_product_scope'] [411]; MANUFACTURE 152053658 UNKNOWN ['scope:no_product_scope'] [412]; ANALYSIS 034060843 UNKNOWN ['scope:no_product_scope'] [413]; ANALYSIS 961097503 UNKNOWN ['scope:no_product_scope'] [414].
- Premise holds: **yes**; expectation holds: **yes**.

### N7 · MANUFACTURE by an unresolved DUNS

- **Premise:** The only MANUFACTURE assertion for the product names a DUNS absent from every loaded FDA registration file.
- **Expectation:** manufacturing_status UNKNOWN_SITE; the edge is UNKNOWN with reason identity:NOT_FOUND; no FEI; never DIRECT.
- **What it catches:** Promoting an unregistered DUNS to a physical site on the strength of the SPL alone.
- Eligible: 997 products in 804 sets.

#### N19 · `43598-204` amoxicillin and clavulanate potassium
- Label set `58a20183-4eb6-438e-bd1e-a74f4645bb0d` version 7: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/4291f971-d386-411e-8d06-95be682a3961/4291f971-d386-411e-8d06-95be682a3961.xml) (expected XML SHA-256 `416cc3e6667eab1a80f07a01ae4a1e5549a8fd0c99d969012613b2e33a0a5d40`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=58a20183-4eb6-438e-bd1e-a74f4645bb0d). Products in label: 6.
- Raw XML operations naming this product: [('C25391', 'analysis', '214482031'), ('C25391', 'analysis', '595132580'), ('C43360', 'manufacture', '967940441'), ('C82401', 'api manufacture', '214482031'), ('C82401', 'api manufacture', '595132580')]; MANUFACTURE DUNS for it: ['967940441'].
- Graph: manufacturing_status **UNKNOWN_SITE** (EXPLICIT_MANUFACTURE); edges: MANUFACTURE 967940441 UNKNOWN ['identity:NOT_FOUND'] [11912]; API MANUFACTURE 595132580 UNKNOWN ['identity:NOT_FOUND'] [11923]; ANALYSIS 595132580 UNKNOWN ['identity:NOT_FOUND'] [11924]; API MANUFACTURE 214482031 UNKNOWN ['identity:NOT_FOUND'] [11937]; ANALYSIS 214482031 UNKNOWN ['identity:NOT_FOUND'] [11938].
- Premise holds: **yes**; expectation holds: **yes**.

#### N20 · `72934-8170` SALICYLIC ACID 2% /SODIUM SULFACETAMIDE MONOHYDRATE 8%
- Label set `87395273-37fa-7cef-e053-2991aa0a54c6` version 1: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/87390b9e-a525-2e36-e053-2a91aa0affe2/87390b9e-a525-2e36-e053-2a91aa0affe2.xml) (expected XML SHA-256 `fbd86b136cf263f531a1d7b2d78a6dfe1645b7dee3ac73e864c226634538eb54`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=87395273-37fa-7cef-e053-2991aa0a54c6). Products in label: 1.
- Raw XML operations naming this product: [('C43360', 'manufacture', '080105003')]; MANUFACTURE DUNS for it: ['080105003'].
- Graph: manufacturing_status **UNKNOWN_SITE** (EXPLICIT_MANUFACTURE); edges: MANUFACTURE 080105003 UNKNOWN ['identity:NOT_FOUND'] [16011].
- Premise holds: **yes**; expectation holds: **yes**.

#### N21 · `52565-096` ZANTAC
- Label set `95dc4515-7690-4881-ae14-9f8655a68dfe` version 4: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/4a3400a1-5ac0-407f-b4c9-cc75b5da4b82/4a3400a1-5ac0-407f-b4c9-cc75b5da4b82.xml) (expected XML SHA-256 `61d3d399ed5bf7a014b3b5ed52e688b7c69dd5dd54007c24aa0b5ff616a832a8`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=95dc4515-7690-4881-ae14-9f8655a68dfe). Products in label: 1.
- Raw XML operations naming this product: [('C43360', 'manufacture', '011036910')]; MANUFACTURE DUNS for it: ['011036910'].
- Graph: manufacturing_status **UNKNOWN_SITE** (EXPLICIT_MANUFACTURE); edges: MANUFACTURE 011036910 UNKNOWN ['identity:NOT_FOUND'] [18897].
- Premise holds: **yes**; expectation holds: **yes**.

### N8 · MANUFACTURE by a stale-registration DUNS

- **Premise:** The only MANUFACTURE assertion names a DUNS listed in an archived registration file but not the current one.
- **Expectation:** manufacturing_status TENTATIVE; the edge is TENTATIVE with reason identity:STALE_REGISTERED; never DIRECT.
- **What it catches:** Reporting a site whose registration has lapsed as currently confirmed.
- Eligible: 362 products in 285 sets.

#### N22 · `60615-0001` Oxygen
- Label set `448541b9-f1f2-431c-bfaf-e43408724bac` version 8: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/2731ab40-aa4b-3a50-e063-6394a90a0860/2731ab40-aa4b-3a50-e063-6394a90a0860.xml) (expected XML SHA-256 `5de7f96b6feb7d80fb83b0d8ee46c02080720428212d17c4c6a57048e020cc8a`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=448541b9-f1f2-431c-bfaf-e43408724bac). Products in label: 1.
- Raw XML operations naming this product: [('C43360', 'manufacture', '147318815')]; MANUFACTURE DUNS for it: ['147318815'].
- Graph: manufacturing_status **TENTATIVE** (EXPLICIT_MANUFACTURE); edges: MANUFACTURE 147318815 TENTATIVE ['identity:STALE_REGISTERED'] [56324].
- Premise holds: **yes**; expectation holds: **yes**.

#### N23 · `84778-114` Salkalli
- Label set `4301f19f-aa6c-c143-e063-6394a90aedb0` version 1: [FDA SPL XML by document ID](https://www.accessdata.fda.gov/spl/data/43030b30-bd8d-0869-e063-6294a90aa52b/43030b30-bd8d-0869-e063-6294a90aa52b.xml) (expected XML SHA-256 `13094cc8cff1ade9a774c7eb1e231498f8c20839034b49bdb2457bb99314e107`), [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=4301f19f-aa6c-c143-e063-6394a90aedb0). Products in label: 1.
- Raw XML operations naming this product: [('C43360', 'manufacture', '455800881'), ('C84732', 'label', '455800881')]; MANUFACTURE DUNS for it: ['455800881'].
- Graph: manufacturing_status **TENTATIVE** (EXPLICIT_MANUFACTURE); edges: LABEL 455800881 TENTATIVE ['identity:STALE_REGISTERED'] [94814]; MANUFACTURE 455800881 TENTATIVE ['identity:STALE_REGISTERED'] [94815].
- Premise holds: **yes**; expectation holds: **yes**.

## Summary

23 controls: premise holds for 23, expectation holds for 23. By type: {'N1': 3, 'N2': 3, 'N3': 3, 'N4': 3, 'N5': 3, 'N6': 3, 'N7': 3, 'N8': 2}.

A human audit of these controls records, per control, whether the label really contains the premise and whether the explorer shows the expectation. Verdicts go in a new CSV, not in `docs/human_audit_verdicts.csv`.
