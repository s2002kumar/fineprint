# Coverage sample: per-case digest (generated; read-only input to adjudication)

Generated 2026-10-22T09:28:32Z from the frozen manifest (SHA-256 `560a3fddde09db63…`). Full detail in `coverage_cases.json`.

## S001 · OTHER_OPERATIONS_ONLY · `63187-023` Silver Sulfadiazine
- set `532d776e-54b3-4d4f-bb7a-94927bfba4d2` v7 (published 2024-03-11, effective 20240301); labeler ['Proficient Rx LP']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Proficient Rx LP', '079196022')]
- ops for this product: [('C73606', 'REPACK', '079196022'), ('C73607', 'RELABEL', '079196022')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['67877-124'].
- identity: 079196022 CURRENT_REGISTERED FEI 3011557028 (Proficient Rx LP)
- DailyMed today: latest v7 (7 versions); sampled version listed: True, published 2024-03-11
- free text (3 hits):
  - [MANUFACTURED_FOR] §34069-5 HOW SUPPLIED @191: “Manufactured for: Ascend Laboratories, LLCMontvale, NJ 07645”
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @252: “Manufactured by: Crown Laboratories, Inc.Johnson City, TN 37604”
  - [RELABELED_BY] §34069-5 HOW SUPPLIED @316: “Relabeled by: Proficient Rx LPThousand Oaks, CA 91320”
  - baseline: MANUFACTURED_FOR → company “Ascend Laboratories” | location “LLCMontvale, NJ 07645” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Crown Laboratories” | location “Inc.Johnson City, TN 37604” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: RELABELED_BY → company “Proficient Rx LPThousand Oaks” | location “CA 91320” | label-establishment name match: False; DECRS exact-name rows: 0

## S002 · OTHER_OPERATIONS_ONLY · `61919-015` AMOXICILLIN
- set `8b28d3ac-0d6a-456b-a428-9ec6fe061d95` v3 (published 2020-01-21, effective 20200117); labeler ['DIRECT RX']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('DIRECT RX', '079254320')]
- ops for this product: [('C73607', 'relabel', '079254320')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0143-9889'].
- identity: 079254320 CURRENT_REGISTERED FEI 3011690045 (Direct Rx)
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2020-01-21
- free text (2 hits):
  - [DISTRIBUTED_BY] §68498-5 PATIENT MEDICATION INFORMATION SECTION @1557: “Distributed by: West-Ward Pharmaceutical Corp. Eatontown, NJ 07724 USA”
  - [MANUFACTURED_BY] §68498-5 PATIENT MEDICATION INFORMATION SECTION @1628: “Manufactured by: HIKMA Pharmaceuticals P.O. Box 182400 Amman 11118 – Jordan”
  - baseline: DISTRIBUTED_BY → company “West-Ward Pharmaceutical Corp” | location “Eatontown, NJ 07724 USA” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “HIKMA Pharmaceuticals P” | location “O. Box 182400 Amman 11118 – Jordan” | label-establishment name match: False; DECRS exact-name rows: 0

## S003 · OTHER_OPERATIONS_ONLY · `71205-439` celecoxib
- set `0ad14a4e-2f05-4ce7-93d1-1cb7e4d8f7d0` v2 (published 2022-08-29, effective 20220801); labeler ['Proficient Rx LP']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Proficient Rx LP', '079196022')]
- ops for this product: [('C73606', 'REPACK', '079196022'), ('C73607', 'RELABEL', '079196022')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['33342-156'].
- identity: 079196022 CURRENT_REGISTERED FEI 3011557028 (Proficient Rx LP)
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2022-08-29
- free text (6 hits):
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @3287: “Manufactured for : Macleods Pharma USA, Inc. Plainsboro, NJ 08536”
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @3353: “Manufactured by: Macleods Pharmaceuticals Ltd. Baddi, Himachal Pradesh, INDIA”
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @3431: “Repackaged by: Proficient Rx LP Thousand Oaks, CA 91320 Revision Date: June 2019”
  - [MANUFACTURED_FOR] §42231-1 . @5313: “Manufactured for: Macleods Pharma USA, Inc. Plainsboro, NJ 08536”
  - [MANUFACTURED_BY] §42231-1 . @5378: “Manufactured by: Macleods Pharmaceuticals Ltd. Baddi, Himachal Pradesh, INDIA”
  - [REPACKAGED_BY] §42231-1 . @5456: “Repackaged by: Proficient Rx LP Thousand Oaks, CA 91320 Revision Date: June 2019”
  - baseline: MANUFACTURED_FOR → company “Macleods Pharma USA” | location “Inc. Plainsboro, NJ 08536” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Macleods Pharmaceuticals Ltd” | location “Baddi, Himachal Pradesh, INDIA” | label-establishment name match: False; DECRS exact-name rows: 5
  - baseline: REPACKAGED_BY → company “Proficient Rx LP Thousand Oaks” | location “CA 91320 Revision Date: June 2019” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Macleods Pharma USA” | location “Inc. Plainsboro, NJ 08536” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Macleods Pharmaceuticals Ltd” | location “Baddi, Himachal Pradesh, INDIA” | label-establishment name match: False; DECRS exact-name rows: 5
  - baseline: REPACKAGED_BY → company “Proficient Rx LP Thousand Oaks” | location “CA 91320 Revision Date: June 2019” | label-establishment name match: False; DECRS exact-name rows: 0

## S004 · OTHER_OPERATIONS_ONLY · `87063-187` METOPROLOL TARTRATE
- set `df3492c3-b71a-40d8-838b-031ebca969d8` v1 (published 2026-05-21, effective 20260518); labeler ['ASCLEMED USA INC.']; 5 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('ASCLEMED USA INC. DBA ENOVACHEM', '059888437')]
- ops for this product: [('C73606', 'repack', '059888437'), ('C73607', 'relabel', '059888437')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['72888-211'].
- identity: 059888437 CURRENT_REGISTERED FEI 3001452204 (ASCLEMED USA INC. DBA ENOVACHEM)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2026-05-21
- free text (1 hits):
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @910: “Repackaged by: Enovachem PHARMACEUTICALS Torrance, CA 90501”
  - baseline: REPACKAGED_BY → company “Enovachem PHARMACEUTICALS Torrance” | location “CA 90501” | label-establishment name match: False; DECRS exact-name rows: 0

## S005 · OTHER_OPERATIONS_ONLY · `72789-174` Lithium Carbonate
- set `d20ed2aa-aa56-4709-9e7a-9243c71465c9` v26 (published 2025-01-20, effective 20250117); labeler ['PD-Rx Pharmaceuticals, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('PD-Rx Pharmaceuticals, Inc.', '156893695')]
- ops for this product: [('C73606', 'repack', '156893695')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0054-4527'].
- identity: 156893695 CURRENT_REGISTERED FEI 1641825 (PD-Rx Pharmaceuticals Inc.)
- DailyMed today: latest v27 (6 versions); sampled version listed: True, published 2025-01-20; NEWER VERSION EXISTS
- free text: no manufacturing-role statement found

## S006 · OTHER_OPERATIONS_ONLY · `72189-066` VENLAFAXINE HYDROCHLORIDE
- set `9b8e27ef-e460-604f-e053-2a95a90a7bbf` v1 (published 2020-01-08, effective 20200107); labeler ['DIRECT RX']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('DIRECT RX', '079254320')]
- ops for this product: [('C73606', 'repack', '079254320')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['65862-697'].
- identity: 079254320 CURRENT_REGISTERED FEI 3011690045 (Direct Rx)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2020-01-08
- free text (2 hits):
  - [DISTRIBUTED_BY] §88436-1  @14080: “Distributed by: Aurobindo Pharma USA, Inc. 279 Princeton-Hightstown Road East Windsor, NJ 08520”
  - [MANUFACTURED_BY] §88436-1  @14176: “Manufactured by: Aurobindo Pharma Limited Hyderabad-500 038, India”
  - baseline: DISTRIBUTED_BY → company “Aurobindo Pharma USA” | location “Inc. 279 Princeton-Hightstown Road East Windsor, NJ 08520” | label-establishment name match: False; DECRS exact-name rows: 4
  - baseline: MANUFACTURED_BY → company “Aurobindo Pharma Limited Hyderabad-500 038” | location “India” | label-establishment name match: False; DECRS exact-name rows: 0

## S007 · OTHER_OPERATIONS_ONLY · `51662-1574` FUROSEMIDE
- set `c5db4434-0b47-038c-e053-2995a90ad7fe` v6 (published 2024-01-30, effective 20240128); labeler ['HF Acquisition Co LLC, DBA HealthFirst']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('HF Acquisition Co LLC, DBA HealthFirst', '045657305')]
- ops for this product: [('C73607', 'relabel', '045657305')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['63323-280'].
- identity: 045657305 CURRENT_REGISTERED FEI 3014534 (HF Acquisition Co LLC)
- DailyMed today: latest v6 (5 versions); sampled version listed: True, published 2024-01-30
- free text: no manufacturing-role statement found

## S008 · OTHER_OPERATIONS_ONLY · `43353-298` lisinopril
- set `32eb18bc-a80d-4de1-8f38-e591d8f66870` v4 (published 2021-08-11, effective 20210810); labeler ['Aphena Pharma Solutions - Tennessee, LLC']; 5 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Aphena Pharma Solutions - Tennessee, LLC', '128385585')]
- ops for this product: [('C73606', 'REPACK', '128385585')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['76282-418'].
- identity: 128385585 CURRENT_REGISTERED FEI 3003849479 (Aphena Pharma Solutions - Tennessee, LLC)
- DailyMed today: latest v4 (4 versions); sampled version listed: True, published 2021-08-11
- free text (3 hits):
  - [MANUFACTURED_FOR] §34069-5 HOW SUPPLIED @2917: “Manufactured for:Exelan Pharmaceuticals, Inc.Lawrenceville, GA 30046”
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @2986: “Manufactured by:InvaGen Pharmaceuticals, Inc.Hauppauge, NY 11788 Rev: 11/13 Barcode: 422-11-2013”
  - [REPACKAGED_BY] §42229-5 Repackaging Information @821: “Repackaged by: Cookeville, TN 38506 20170629JH”
  - baseline: MANUFACTURED_FOR → company “Exelan Pharmaceuticals” | location “Inc.Lawrenceville, GA 30046” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “InvaGen Pharmaceuticals” | location “Inc.Hauppauge, NY 11788 Rev: 11/13 Barcode: 422-11-2013” | label-establishment name match: False; DECRS exact-name rows: 5
  - baseline: REPACKAGED_BY → company “Cookeville” | location “TN 38506 20170629JH” | label-establishment name match: False; DECRS exact-name rows: 0

## S009 · OTHER_OPERATIONS_ONLY · `71335-2711` Minocycline Hydrochloride
- set `ddd22f2c-050b-4776-912b-39b3e6202c75` v100 (published 2025-07-31, effective 20250728); labeler ['Bryant Ranch Prepack']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Bryant Ranch Prepack', '171714327')]
- ops for this product: [('C73606', 'REPACK', '171714327'), ('C73607', 'RELABEL', '171714327')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['67877-578'].
- identity: 171714327 CURRENT_REGISTERED FEI 1000519407 (Bryant Ranch Prepack)
- DailyMed today: latest v100 (1 versions); sampled version listed: True, published 2025-07-31
- free text (5 hits):
  - [RELABELED_BY] §34069-5 16 HOW SUPPLIED/STORAGE AND HANDLING @763: “Relabeled by: Bryant Ranch Prepack, Inc. Burbank, CA 91504”
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2889: “Manufactured by: Alkem Laboratories Ltd., Mumbai - 400 013, INDIA.”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2956: “Distributed by: Ascend Laboratories, LLC Bedminster, NJ 07921”
  - [MANUFACTURED_BY] §42229-5 PATIENT INFORMATION @12077: “Manufactured by: Alkem Laboratories Ltd., Mumbai - 400 013, INDIA.”
  - [DISTRIBUTED_BY] §42229-5 PATIENT INFORMATION @12144: “Distributed by: Ascend Laboratories, LLC Bedminster, NJ 07921”
  - baseline: RELABELED_BY → company “Bryant Ranch Prepack” | location “Inc. Burbank, CA 91504” | label-establishment name match: True; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Alkem Laboratories Ltd” | location “, Mumbai - 400 013, INDIA” | label-establishment name match: False; DECRS exact-name rows: 4
  - baseline: DISTRIBUTED_BY → company “Ascend Laboratories” | location “LLC Bedminster, NJ 07921” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Alkem Laboratories Ltd” | location “, Mumbai - 400 013, INDIA” | label-establishment name match: False; DECRS exact-name rows: 4
  - baseline: DISTRIBUTED_BY → company “Ascend Laboratories” | location “LLC Bedminster, NJ 07921” | label-establishment name match: False; DECRS exact-name rows: 0

## S010 · OTHER_OPERATIONS_ONLY · `53401-015` METOPROLOL TARTRATE
- set `54754388-39c9-9a02-e063-6394a90a90b3` v1 (published 2026-06-18, effective 20260617); labeler ['Aphena Pharma Solutions - Tennessee, LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Aphena Pharma Solutions - Tennessee, LLC', '128385585')]
- ops for this product: [('C73606', 'repack', '128385585')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['76282-794'].
- identity: 128385585 CURRENT_REGISTERED FEI 3003849479 (Aphena Pharma Solutions - Tennessee, LLC)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2026-06-18
- free text (3 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @895: “Manufactured by: Rubicon Research Ltd., Thane 421506, India.”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @956: “Distributed by: Exelan Pharmaceuticals, Inc. Boca Raton, FL 33432”
  - [REPACKAGED_BY] §42229-5 REPACKAGING INFORMATION @789: “Repackaged by: Cookeville, TN 38506 20260617AMH”
  - baseline: MANUFACTURED_BY → company “Rubicon Research Ltd” | location “, Thane 421506, India” | label-establishment name match: False; DECRS exact-name rows: 4
  - baseline: DISTRIBUTED_BY → company “Exelan Pharmaceuticals” | location “Inc. Boca Raton, FL 33432” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Cookeville” | location “TN 38506 20260617AMH” | label-establishment name match: False; DECRS exact-name rows: 0

## S011 · OTHER_OPERATIONS_ONLY · `68788-7339` Cefdinir
- set `c3892cd7-0e98-4ba3-a845-4aedf6c2a830` v8 (published 2026-03-26, effective 20260324); labeler ['Preferred Pharmaceuticals Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Preferred Pharmaceuticals Inc.', '791119022')]
- ops for this product: [('C73606', 'REPACK', '791119022')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['57237-099'].
- identity: 791119022 CURRENT_REGISTERED FEI 3004582966 (Preferred Pharmaceuticals Inc.)
- DailyMed today: latest v8 (8 versions); sampled version listed: True, published 2026-03-26
- free text (4 hits):
  - [DISTRIBUTED_BY] §34093-5 REFERENCES @692: “Distributed by: Rising Health, LLC Saddle Brook, NJ 07663”
  - [MADE_IN] §34093-5 REFERENCES @750: “Made in India Code: TS/DRUGS/78/1996”
  - [REPACKAGED_BY] §34093-5 REFERENCES @804: “Repackaged By: Preferred Pharmaceuticals Inc.”
  - [REPACKAGED_BY] §51945-4 PACKAGE LABEL-PRINCIPAL DISPLAY PANEL -300 mg @63: “Repackaged By: Preferred Pharmaceuticals Inc.”
  - baseline: DISTRIBUTED_BY → company “Rising Health” | location “LLC Saddle Brook, NJ 07663” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “India Code: TS/DRUGS/78/1996” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Preferred Pharmaceuticals Inc” | location “” | label-establishment name match: True; DECRS exact-name rows: 1
  - baseline: REPACKAGED_BY → company “Preferred Pharmaceuticals Inc” | location “” | label-establishment name match: True; DECRS exact-name rows: 1

## S012 · OTHER_OPERATIONS_ONLY · `68071-1548` Valacyclovir Hydrochloride
- set `552b806d-97d2-364d-e054-00144ff8d46c` v4 (published 2025-05-30, effective 20250528); labeler ['NuCare Pharmacuticals,Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('NuCare Pharmaceuticals,Inc.', '010632300')]
- ops for this product: [('C73607', 'relabel', '010632300')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['57237-043'].
- identity: 010632300 CURRENT_REGISTERED FEI 3003294404 (NuCare Pharmaceuticals,Inc.)
- DailyMed today: latest v4 (4 versions); sampled version listed: True, published 2025-05-30
- free text (4 hits):
  - [DISTRIBUTED_BY] §42229-5 17.5 Chickenpox @96: “Distributed by: Citron Pharma LLC Suite -1101 2 Tower Center Blvd East Brunswick NJ 08816 Code No.: DRUGS/AP/22/2009”
  - [MADE_IN] §42229-5 17.5 Chickenpox @213: “Made in India”
  - [DISTRIBUTED_BY] §42230-3 PATIENT INFORMATION @9496: “Distributed by: Citron Pharma LLC Suite -1101 2 Tower Center Blvd East Brunswick NJ 08816 Code No.: DRUGS/AP/22/2009”
  - [MADE_IN] §42230-3 PATIENT INFORMATION @9613: “Made in India”
  - baseline: DISTRIBUTED_BY → company “Citron Pharma LLC Suite -1101 2 Tower Center Blvd East Brunswick NJ 08816 Code N” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “India” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Citron Pharma LLC Suite -1101 2 Tower Center Blvd East Brunswick NJ 08816 Code N” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “India” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S013 · OTHER_OPERATIONS_ONLY · `67296-1917` Tramadol Hydrochloride
- set `1e047b6c-7523-3619-e063-6394a90a03fc` v1 (published 2024-07-26, effective 20240724); labeler ['RedPharm Drug']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('RedPharm Drug', '828374897')]
- ops for this product: [('C73606', 'repack', '828374897')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['72888-008'].
- identity: 828374897 CURRENT_REGISTERED FEI 3003719240 (RedPharm Drug)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2024-07-26
- free text (4 hits):
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @9228: “Distributed By: Advagen Pharma Ltd 666 Plainsboro Road Plainsboro Suite 605, Plainsboro, NJ, 08536, USA”
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @9332: “Manufactured by: Rubicon Research Private Limited, Ambernath,”
  - [DISTRIBUTED_BY] §42231-1  @5824: “Distributed By: Advagen Pharma Ltd 666 Plainsboro Road Plainsboro Suite 605, Plainsboro, NJ, 08536, USA”
  - [MANUFACTURED_BY] §42231-1  @5928: “Manufactured by: Rubicon Research Private Limited, Ambernath,”
  - baseline: DISTRIBUTED_BY → company “Advagen Pharma Ltd 666 Plainsboro Road Plainsboro Suite 605” | location “Plainsboro, NJ, 08536, USA” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Rubicon Research Private Limited” | location “Ambernath” | label-establishment name match: False; DECRS exact-name rows: 4
  - baseline: DISTRIBUTED_BY → company “Advagen Pharma Ltd 666 Plainsboro Road Plainsboro Suite 605” | location “Plainsboro, NJ, 08536, USA” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Rubicon Research Private Limited” | location “Ambernath” | label-establishment name match: False; DECRS exact-name rows: 4

## S014 · OTHER_OPERATIONS_ONLY · `67046-1481` Diltiazem Hydrochloride
- set `2ced821f-19a6-4c7e-e063-6394a90adb80` v1 (published 2025-01-31, effective 20250130); labeler ['Coupler LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Coupler LLC', '119003108')]
- ops for this product: [('C73606', 'repack', '119003108')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0378-6120'].
- identity: 119003108 CURRENT_REGISTERED FEI 3003734940 (Coupler LLC)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2025-01-31
- free text (2 hits):
  - [MANUFACTURED_FOR] §34069-5 HOW SUPPLIED @1406: “Manufactured for: Mylan Pharmaceuticals Inc. Morgantown, WV 26505 U.S.A.”
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @1479: “Manufactured by: Mylan Laboratories Limited Hyderabad — 500 096, India 75106328”
  - baseline: MANUFACTURED_FOR → company “Mylan Pharmaceuticals Inc” | location “Morgantown, WV 26505 U.S.A” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Mylan Laboratories Limited Hyderabad — 500 096” | location “India 75106328” | label-establishment name match: False; DECRS exact-name rows: 0

## S015 · OTHER_OPERATIONS_ONLY · `43353-495` Sulfasalazine
- set `a5a23c68-f5bd-42dd-b72c-0641659bae46` v2 (published 2019-12-23, effective 20191218); labeler ['Aphena Pharma Solutions - Tennessee, LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Aphena Pharma Solutions - Tennessee, LLC', '128385585')]
- ops for this product: [('C73606', 'Repack', '128385585')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['59762-5000'].
- identity: 128385585 CURRENT_REGISTERED FEI 3003849479 (Aphena Pharma Solutions - Tennessee, LLC)
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2019-12-23
- free text (2 hits):
  - [REPACKAGED_BY] §34069-5 HOW SUPPLIED @0: “Repackaged by Aphena Pharma Solutions - TN.See Repackaging Information for available configurations. Sulfasalazine tablets, 500 mg, are round, gold-colored, scored tablets, monogrammed "G500". They are available in the f”
  - [REPACKAGED_BY] §42229-5 Repackaging Information @614: “Repackaged by: Cookeville, TN 38506 20140703SC”
  - baseline: REPACKAGED_BY → company “Aphena Pharma Solutions - TN” | location “See Repackaging Information for available configurations. Sulfasalazine tablets,” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Cookeville” | location “TN 38506 20140703SC” | label-establishment name match: False; DECRS exact-name rows: 0

## S016 · OTHER_OPERATIONS_ONLY · `67046-1423` azithromycin dihydrate
- set `26a53662-282d-b5da-e063-6394a90a6a4b` v1 (published 2024-11-15, effective 20241111); labeler ['Coupler LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Coupler LLC', '119003108')]
- ops for this product: [('C73606', 'repack', '119003108')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['68180-862'].
- identity: 119003108 CURRENT_REGISTERED FEI 3003734940 (Coupler LLC)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2024-11-15
- free text (4 hits):
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @1661: “Manufactured for: Lupin Pharmaceuticals, Inc. Baltimore, Maryland 21202 United States”
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1747: “Manufactured by: Lupin Limited Goa - 403722 India”
  - [MANUFACTURED_FOR] §42230-3  @9389: “Manufactured for: Lupin Pharmaceuticals, Inc. Baltimore, Maryland 21202 United States”
  - [MANUFACTURED_BY] §42230-3  @9475: “Manufactured by: Lupin Limited Goa - 403722 India”
  - baseline: MANUFACTURED_FOR → company “Lupin Pharmaceuticals” | location “Inc. Baltimore, Maryland 21202 United States” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Lupin Limited Goa - 403722 India” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Lupin Pharmaceuticals” | location “Inc. Baltimore, Maryland 21202 United States” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Lupin Limited Goa - 403722 India” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S017 · OTHER_OPERATIONS_ONLY · `68071-3030` meloxicam
- set `87ef5a9b-2dd1-2ef9-e053-2995a90a5149` v6 (published 2025-12-05, effective 20251204); labeler ['NuCare Pharmaceuticals,Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('NuCare Pharmaceuticals,Inc.', '010632300')]
- ops for this product: [('C73606', 'repack', '010632300')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['68382-051'].
- identity: 010632300 CURRENT_REGISTERED FEI 3003294404 (NuCare Pharmaceuticals,Inc.)
- DailyMed today: latest v6 (6 versions); sampled version listed: True, published 2025-12-05
- free text (4 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Cadila Healthcare Ltd. India.”
  - [DISTRIBUTED_BY] §42229-5  @47: “Distributed by: Zydus Pharmaceuticals USA Inc. Pennington, NJ 08534 Rev.: 02/18”
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Cadila Healthcare Ltd. India.”
  - [DISTRIBUTED_BY] §42229-5  @47: “Distributed by: Zydus Pharmaceuticals USA Inc. Pennington, NJ 08534 Rev.: 07/16”
  - baseline: MANUFACTURED_BY → company “Cadila Healthcare Ltd” | location “India” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Zydus Pharmaceuticals USA Inc” | location “Pennington, NJ 08534 Rev.: 02/18” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Cadila Healthcare Ltd” | location “India” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Zydus Pharmaceuticals USA Inc” | location “Pennington, NJ 08534 Rev.: 07/16” | label-establishment name match: False; DECRS exact-name rows: 1

## S018 · OTHER_OPERATIONS_ONLY · `53002-1198` Fluconazole
- set `b00ead0c-c3fc-43a0-bc85-86c6c155635e` v5 (published 2021-06-17, effective 20201215); labeler ['RPK Pharmaceuticals, Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('RPK Pharmaceuticals, Inc.', '147096275')]
- ops for this product: [('C73607', 'RELABEL', '147096275')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['67405-603'].
- identity: 147096275 STALE_REGISTERED FEI 2937511 (RPK Pharmaceuticals, Inc.)
- DailyMed today: latest v5 (3 versions); sampled version listed: True, published 2021-06-17
- free text (2 hits):
  - [MANUFACTURED_FOR] §42229-5  @0: “Manufactured for: HARRIS Pharmaceutical, Inc. Fort Myers, FL 33908 Rev. 04/2019”
  - [MANUFACTURED_FOR] §42230-3  @8417: “Manufactured for: HARRIS Pharmaceutical, Inc. Fort Myers, FL 33908 Rev. 06/2020”
  - baseline: MANUFACTURED_FOR → company “HARRIS Pharmaceutical” | location “Inc. Fort Myers, FL 33908 Rev. 04/2019” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “HARRIS Pharmaceutical” | location “Inc. Fort Myers, FL 33908 Rev. 06/2020” | label-establishment name match: False; DECRS exact-name rows: 0

## S019 · OTHER_OPERATIONS_ONLY · `54868-5671` Synthroid
- set `abe005b2-d962-4ba7-9cb6-a09d35e68ae7` v5 (published 2014-05-07, effective 20140505); labeler ['Physicians Total Care, Inc.']; 12 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Physicians Total Care, Inc.', '194123980')]
- ops for this product: [('C73606', 'repack', '194123980'), ('C73607', 'relabel', '194123980')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0074-3727'].
- identity: 194123980 NOT_FOUND
- DailyMed today: latest v5 (4 versions); sampled version listed: True, published 2014-05-07
- free text: no manufacturing-role statement found

## S020 · OTHER_OPERATIONS_ONLY · `76420-734` Tramadol Hydrochloride
- set `6a60bd36-7dcc-49c3-b6de-b263fdaa312c` v3 (published 2025-08-18, effective 20250814); labeler ['Asclemed USA, Inc.']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('ASCLEMED USA INC. DBA ENOVACHEM', '059888437')]
- ops for this product: [('C73606', 'repack', '059888437'), ('C73607', 'relabel', '059888437')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['72888-008'].
- identity: 059888437 CURRENT_REGISTERED FEI 3001452204 (ASCLEMED USA INC. DBA ENOVACHEM)
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2025-08-18
- free text (2 hits):
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @9242: “Repackaged by: Enovachem PHARMACEUTICALS Torrance, CA 90501”
  - [REPACKAGED_BY] §42231-1  @5838: “Repackaged by: Enovachem PHARMACEUTICALS Torrance, CA 90501 This Medication Guide has been approved by the U.S. Food and Drug Administration.”
  - baseline: REPACKAGED_BY → company “Enovachem PHARMACEUTICALS Torrance” | location “CA 90501” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Enovachem PHARMACEUTICALS Torrance” | location “CA 90501 This Medication Guide has been approved by the U.S. Food and Drug Admin” | label-establishment name match: False; DECRS exact-name rows: 0

## S021 · OTHER_OPERATIONS_ONLY · `76420-812` Bupropion Hydrochloride
- set `637e89e5-8f6e-4392-8045-a778cb9ed138` v2 (published 2025-02-17, effective 20250212); labeler ['Asclemed USA, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('ASCLEMED USA INC. DBA ENOVACHEM', '059888437')]
- ops for this product: [('C73606', 'repack', '059888437'), ('C73607', 'relabel', '059888437')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['45963-142'].
- identity: 059888437 CURRENT_REGISTERED FEI 3001452204 (ASCLEMED USA INC. DBA ENOVACHEM)
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2025-02-17
- free text (2 hits):
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @7041: “Repackaged by: Enovachem PHARMACEUTICALS Torrance, CA 90501”
  - [REPACKAGED_BY] §42231-1  @19638: “Repackaged by: Enovachem PHARMACEUTICALS Torrance, CA 90501 This Medication Guide has been approved by the U.S. Food and Drug Administration.Rev. F 12/2023”
  - baseline: REPACKAGED_BY → company “Enovachem PHARMACEUTICALS Torrance” | location “CA 90501” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Enovachem PHARMACEUTICALS Torrance” | location “CA 90501 This Medication Guide has been approved by the U.S. Food and Drug Admin” | label-establishment name match: False; DECRS exact-name rows: 0

## S022 · OTHER_OPERATIONS_ONLY · `82457-003` Nitrogen
- set `07dcb683-a5e9-b016-e063-6394a90a746d` v3 (published 2025-11-17, effective 20251029); labeler ['Toll Company']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Toll Company', '052740669')]
- ops for this product: [('C73606', 'repack', '052740669')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['82666-002'].
- identity: 052740669 CURRENT_REGISTERED FEI 3004660914 (Toll Company)
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2025-11-17
- free text: no manufacturing-role statement found

## S023 · OTHER_OPERATIONS_ONLY · `71335-1759` Pioglitazone
- set `466ef4c8-84d4-4ded-8505-a33f12adf31c` v103 (published 2026-03-10, effective 20260309); labeler ['Bryant Ranch Prepack']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Bryant Ranch Prepack', '171714327')]
- ops for this product: [('C73606', 'REPACK', '171714327'), ('C73607', 'RELABEL', '171714327')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['57237-221'].
- identity: 171714327 CURRENT_REGISTERED FEI 1000519407 (Bryant Ranch Prepack)
- DailyMed today: latest v103 (4 versions); sampled version listed: True, published 2026-03-10
- free text (5 hits):
  - [RELABELED_BY] §34069-5 16 HOW SUPPLIED/STORAGE AND HANDLING @458: “Relabeled by:Bryant Ranch PrepackBurbank, CA 91504”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1763: “Distributed by: Rising Health, LLC Saddle Brook, NJ 07663”
  - [MADE_IN] §34076-0 17 PATIENT COUNSELING INFORMATION @1821: “Made in India Code: TS/DRUGS/19/1993”
  - [DISTRIBUTED_BY] §42231-1 MEDICATION GUIDE @9106: “Distributed by: Rising Health, LLC Saddle Brook, NJ 07663”
  - [MADE_IN] §42231-1 MEDICATION GUIDE @9164: “Made in India Code: TS/DRUGS/19/1993”
  - baseline: RELABELED_BY → company “Bryant Ranch PrepackBurbank” | location “CA 91504” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Rising Health” | location “LLC Saddle Brook, NJ 07663” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “India Code: TS/DRUGS/19/1993” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Rising Health” | location “LLC Saddle Brook, NJ 07663” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “India Code: TS/DRUGS/19/1993” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S024 · OTHER_OPERATIONS_ONLY · `17856-0036` Sodium Polystyrene Sulfonate
- set `34fe6cd2-70f1-4ea3-adb7-a3e37defc886` v2 (published 2016-05-04, effective 20160504); labeler ['Atlantic Biologicals Corps']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Atlantic Biologicals Corps', '047437707')]
- ops for this product: [('C73606', 'REPACK', '047437707'), ('C73607', 'RELABEL', '047437707')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['10702-036'].
- identity: 047437707 STALE_REGISTERED FEI 3010166262 (Atlantic Biologicals)
- DailyMed today: latest v2 (1 versions); sampled version listed: True, published 2016-05-04
- free text: no manufacturing-role statement found

## S025 · OTHER_OPERATIONS_ONLY · `68151-2049` Tolterodine Tartrate
- set `09b4ec42-9b47-4a6c-b219-7c5dcda35ac5` v4 (published 2017-12-27, effective 20171226); labeler ['Carilion Materials Management']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / OTHER_OPERATIONS_ONLY.
- establishments: [('Carilion Materials Management', '079239644')]
- ops for this product: [('C73606', 'REPACK', '079239644')]; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0093-2049'].
- identity: 079239644 NOT_FOUND
- DailyMed today: latest v4 (2 versions); sampled version listed: True, published 2017-12-27
- free text (2 hits):
  - [MANUFACTURED_FOR] §42230-3  @7139: “Manufactured For: TEVA PHARMACEUTICALS USA, INC. North Wales, PA 19454By Pfizer Inc, New York, NY 10017 LAB-0607-3.0”
  - [MANUFACTURED_FOR] §42230-3  @7139: “Manufactured For: TEVA PHARMACEUTICALS USA, INC. North Wales, PA 19454By Pfizer Inc, New York, NY 10017 LAB-0608-3.0March 2015”
  - baseline: MANUFACTURED_FOR → company “TEVA PHARMACEUTICALS USA” | location “INC. North Wales, PA 19454By Pfizer Inc, New York, NY 10017 LAB-0607-3.0” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “TEVA PHARMACEUTICALS USA” | location “INC. North Wales, PA 19454By Pfizer Inc, New York, NY 10017 LAB-0608-3.0March 20” | label-establishment name match: False; DECRS exact-name rows: 1

## S026 · NO_ESTABLISHMENT_BLOCK · `49884-302` Oxandrolone
- set `a6f42739-5bfc-4b76-8795-e93fa58f3d29` v12 (published None, effective 20220307); labeler ['Par Pharmaceutical, Inc.']; 2 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v12 (10 versions); sampled version listed: True, published 2023-07-07
- free text (1 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @438: “Manufactured by: Par Pharmaceutical Chestnut Ridge, NY 10977”
  - baseline: MANUFACTURED_BY → company “Par Pharmaceutical Chestnut Ridge” | location “NY 10977” | label-establishment name match: False; DECRS exact-name rows: 0

## S027 · NO_ESTABLISHMENT_BLOCK · `55154-4783` Losartan Potassium
- set `021cd76a-b093-4704-8410-5e7d01e20a54` v21 (published 2026-09-07, effective 20260827); labeler ['Cardinal Health 107, LLC']; 3 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['68084-346'].
- DailyMed today: latest v21 (21 versions); sampled version listed: True, published 2026-09-07
- free text (4 hits):
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @663: “Distributed by: American Health Packaging Columbus, OH 43217”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @724: “Distributed By: Cardinal Health Dublin, OH 43017 L48539901024 L44917830624 L49312000324 8234601/0426”
  - [DISTRIBUTED_BY] §42230-3 Patient Information @7327: “Distributed by: American Health Packaging Columbus, OH 43217”
  - [DISTRIBUTED_BY] §42230-3 Patient Information @7388: “Distributed By: Cardinal Health Dublin, OH 43017 L48539901024 L44917830624 L49312000324 8234601/0426”
  - baseline: DISTRIBUTED_BY → company “American Health Packaging Columbus” | location “OH 43217” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Cardinal Health Dublin” | location “OH 43017 L48539901024 L44917830624 L49312000324 8234601/0426” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “American Health Packaging Columbus” | location “OH 43217” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Cardinal Health Dublin” | location “OH 43017 L48539901024 L44917830624 L49312000324 8234601/0426” | label-establishment name match: False; DECRS exact-name rows: 0

## S028 · NO_ESTABLISHMENT_BLOCK · `49502-345` TOBI
- set `6a3c3871-1d3a-44d6-8be3-526b30123ef7` v7 (published 2026-06-29, effective 20251115); labeler ['Viatris Specialty LLC']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v7 (5 versions); sampled version listed: True, published 2026-06-29
- free text (5 hits):
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1225: “Distributed by: Viatris Specialty LLC Morgantown, WV 26505 U.S.A. © 2025 Viatris Inc. TOBI is a registered trademark of BGP Products Operations GmbH, a Viatris Company. The brands listed are trademarks of their respectiv”
  - [DISTRIBUTED_BY] §42230-3 PATIENT INFORMATION @6998: “Distributed by: Viatris Specialty LLC Morgantown, WV 26505 U.S.A. © 2025 Viatris Inc. TOBI is a registered trademark of BGP Products Operations GmbH, a Viatris Company. The brands listed are trademarks of their respectiv”
  - [DISTRIBUTED_BY] §59845-8 Instructions for Use @7723: “Distributed by: Viatris Specialty LLC Morgantown, WV 26505 U.S.A. © 2025 Viatris Inc. TOBI is a registered trademark of BGP Products Operations GmbH, a Viatris Company. The brands listed are trademarks of their respectiv”
  - [MANUFACTURED_FOR] §51945-4 PRINCIPAL DISPLAY PANEL – 300 mg / 5 mL Ampules @660: “Manufactured for: Viatris Specialty LLC Morgantown, WV 26505 U.S.A.”
  - [MANUFACTURED_BY] §51945-4 PRINCIPAL DISPLAY PANEL – 300 mg / 5 mL Ampules @728: “Manufactured by: Woodstock Sterile Solutions, Inc. Woodstock, IL 60098 U.S.A.”
  - baseline: DISTRIBUTED_BY → company “Viatris Specialty LLC Morgantown” | location “WV 26505 U.S.A. © 2025 Viatris Inc. TOBI is a registered trademark of BGP Produc” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Viatris Specialty LLC Morgantown” | location “WV 26505 U.S.A. © 2025 Viatris Inc. TOBI is a registered trademark of BGP Produc” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Viatris Specialty LLC Morgantown” | location “WV 26505 U.S.A. © 2025 Viatris Inc. TOBI is a registered trademark of BGP Produc” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Viatris Specialty LLC Morgantown” | location “WV 26505 U.S.A” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Woodstock Sterile Solutions” | location “Inc. Woodstock, IL 60098 U.S.A” | label-establishment name match: False; DECRS exact-name rows: 1

## S029 · NO_ESTABLISHMENT_BLOCK · `70710-1184` Dextroamphetamine Saccharate, Amphetamine Aspartate Monohydrate, Dextroamphetamine Sulfate and Amphetamine Sulfate
- set `a6eb907b-f830-4603-9899-e0ecf7d6d862` v8 (published 2021-12-20, effective 20211217); labeler ['Zydus Pharmaceuticals (USA) Inc.']; 6 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v8 (3 versions); sampled version listed: True, published 2021-12-20
- free text (4 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @6036: “Manufactured By: Nesher Pharmaceuticals USA LLC St. Louis, MO 63044”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @6104: “Distributed by: Zydus Pharmaceuticals USA Inc. Pennington, NJ 08534 P10343-3rasub 7/2019 For additional copies of the printed patient information/medication guide, please visit wwww.zydus.com or”
  - [MANUFACTURED_BY] §42229-5 MEDICATION GUIDE @17549: “Manufactured By: Nesher Pharmaceuticals USA LLC St. Louis, MO 63044”
  - [DISTRIBUTED_BY] §42229-5 MEDICATION GUIDE @17617: “Distributed by: Zydus Pharmaceuticals USA Inc. Pennington, NJ 08534 P10343-3rasub 7/2019 This Medication Guide has been approved by the U.S. Food and Drug Administration.”
  - baseline: MANUFACTURED_BY → company “Nesher Pharmaceuticals USA LLC St” | location “Louis, MO 63044” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Zydus Pharmaceuticals USA Inc” | location “Pennington, NJ 08534 P10343-3rasub 7/2019 For additional copies of the printed p” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Nesher Pharmaceuticals USA LLC St” | location “Louis, MO 63044” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Zydus Pharmaceuticals USA Inc” | location “Pennington, NJ 08534 P10343-3rasub 7/2019 This Medication Guide has been approve” | label-establishment name match: False; DECRS exact-name rows: 1

## S030 · NO_ESTABLISHMENT_BLOCK · `35561-211` Methocarbamol
- set `d8f10211-f96e-4cf3-9b49-986eb51b703d` v8 (published 2026-02-06, effective 20260204); labeler ['Bostal LLC']; 3 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v8 (6 versions); sampled version listed: True, published 2026-02-06
- free text (1 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @829: “Manufactured by: AustarPharma, LLC 18 Mayfield Ave Edison, NJ 08837, USA”
  - baseline: MANUFACTURED_BY → company “AustarPharma” | location “LLC 18 Mayfield Ave Edison, NJ 08837, USA” | label-establishment name match: False; DECRS exact-name rows: 0

## S031 · NO_ESTABLISHMENT_BLOCK · `0641-6046` Lorazepam
- set `e9b54e42-04cf-4c62-90e1-36f7b31a4e81` v10 (published 2024-04-10, effective 20240409); labeler ['Hikma Pharmaceuticals USA Inc.']; 4 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v10 (8 versions); sampled version listed: True, published 2024-04-10
- free text (1 hits):
  - [MANUFACTURED_BY] §42229-5 ANIMAL TOXICOLOGY AND/OR PHARMACOLOGY @1463: “Manufactured by: Hikma Pharmaceuticals USA Inc. Berkeley Heights, NJ 07922”
  - baseline: MANUFACTURED_BY → company “Hikma Pharmaceuticals USA Inc” | location “Berkeley Heights, NJ 07922” | label-establishment name match: False; DECRS exact-name rows: 5

## S032 · NO_ESTABLISHMENT_BLOCK · `73190-033` nilotinib
- set `4c0bc799-ce6a-822a-e063-6394a90ab748` v1 (published 2026-03-03, effective 20260302); labeler ['AvKARE']; 2 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2026-03-03
- free text (2 hits):
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @5865: “Manufactured for: AvKARE Pulaski, TN 38478”
  - [MANUFACTURED_FOR] §42229-5 Medication Guide @13362: “Manufactured for: AvKARE Pulaski, TN 38478”
  - baseline: MANUFACTURED_FOR → company “AvKARE Pulaski” | location “TN 38478” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “AvKARE Pulaski” | location “TN 38478” | label-establishment name match: False; DECRS exact-name rows: 0

## S033 · NO_ESTABLISHMENT_BLOCK · `73362-101` Yorvipath
- set `a1fa23fd-c434-443e-9a17-5750578c8602` v8 (published 2026-08-17, effective 20260812); labeler ['Ascendis Pharma, Endocrinology, Inc.']; 3 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v8 (5 versions); sampled version listed: True, published 2026-08-17
- free text (2 hits):
  - [MANUFACTURED_BY] §42229-5  @176: “Manufactured by:Ascendis Pharma Bone Diseases A/STuborg Boulevard 12, DK-2900 Hellerup, Denmark For information about YORVIPATH contact:Ascendis Pharma Endocrinology, Inc.Princeton, New Jersey 08540, USA1-844-442-7236 (1”
  - [MANUFACTURED_BY] §42231-1  @9090: “Manufactured by: Ascendis Pharma Bone Diseases A/S, DenmarkYORVIPATH ® is a registered trademark of Ascendis Pharma Group.”
  - baseline: MANUFACTURED_BY → company “Ascendis Pharma Bone Diseases A/STuborg Boulevard 12” | location “DK-2900 Hellerup, Denmark For information about YORVIPATH contact:Ascendis Pharm” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Ascendis Pharma Bone Diseases A/S” | location “DenmarkYORVIPATH ® is a registered trademark of Ascendis Pharma Group” | label-establishment name match: False; DECRS exact-name rows: 0

## S034 · NO_ESTABLISHMENT_BLOCK · `42023-237` Vasostrict
- set `b1147beb-743e-4c62-8927-91192447f8b8` v49 (published 2026-05-20, effective 20260421); labeler ['Par Health USA, LLC']; 5 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v49 (20 versions); sampled version listed: True, published 2026-05-20
- free text (1 hits):
  - [MANUFACTURED_FOR] §42229-5  @0: “Manufactured for: Par Health USA Rochester, MI 48307 © 2025 Par Health, Inc. or one of its affiliates. R12/2025”
  - baseline: MANUFACTURED_FOR → company “Par Health USA Rochester” | location “MI 48307 © 2025 Par Health, Inc. or one of its affiliates. R12/2025” | label-establishment name match: False; DECRS exact-name rows: 0

## S035 · NO_ESTABLISHMENT_BLOCK · `70518-4627` lithium carbonate
- set `01c4facd-ed79-4078-ba33-2044de372d0f` v1 (published 2026-04-28, effective 20260427); labeler ['REMEDYREPACK INC.']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['31722-544'].
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2026-04-28
- free text (5 hits):
  - [DISTRIBUTED_BY] §34069-5 16 HOW SUPPLIED/STORAGE AND HANDLING @506: “Distributed By: Remedy Repack, Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762”
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2982: “Repackaged By /”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2998: “Distributed By: RemedyRepack Inc. 625 Kolter Drive, Indiana, PA 15701 (724) 465-8762”
  - [REPACKAGED_BY] §42231-1 MEDICATION GUIDE @9557: “Repackaged By /”
  - [DISTRIBUTED_BY] §42231-1 MEDICATION GUIDE @9573: “Distributed By: RemedyRepack Inc. 625 Kolter Drive, Indiana, PA 15701 (724) 465-8762”
  - baseline: DISTRIBUTED_BY → company “Remedy Repack” | location “Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “/” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “RemedyRepack Inc” | location “625 Kolter Drive, Indiana, PA 15701 (724) 465-8762” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: REPACKAGED_BY → company “/” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “RemedyRepack Inc” | location “625 Kolter Drive, Indiana, PA 15701 (724) 465-8762” | label-establishment name match: False; DECRS exact-name rows: 1

## S036 · NO_ESTABLISHMENT_BLOCK · `52536-341` Lomustine
- set `3c3637fc-4499-4331-a3c4-6969fc86704e` v2 (published 2026-04-15, effective 20260212); labeler ['Wilshire Pharmaceuticals, Inc.']; 3 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2026-04-15
- free text (1 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2262: “Manufactured by Latina Pharma S.p.A., Sermoneta (LT), Italy for: Wilshire Pharmaceuticals, Inc. Atlanta, GA 30328 USA”
  - baseline: MANUFACTURED_BY → company “Latina Pharma S” | location “p.A., Sermoneta (LT), Italy for: Wilshire Pharmaceuticals, Inc. Atlanta, GA 3032” | label-establishment name match: False; DECRS exact-name rows: 0

## S037 · NO_ESTABLISHMENT_BLOCK · `0338-9147` Dextrose
- set `0bfb32b2-d034-4219-a055-3448f0c424f7` v15 (published 2026-07-06, effective 20210219); labeler ['Baxter Healthcare Company']; 2 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v15 (15 versions); sampled version listed: True, published 2026-07-06
- free text (3 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @510: “Manufactured by, Packed by,”
  - [PACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @527: “Packed by, Distributed by: Baxter Healthcare Corporation Deerfield, IL 60015 USAPrinted in Ireland CB-30-02-662 Baxter, Mini-Bag Plus, and Viaflex are trademarks of Baxter International Inc.”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @538: “Distributed by: Baxter Healthcare Corporation Deerfield, IL 60015 USAPrinted in Ireland CB-30-02-662 Baxter, Mini-Bag Plus, and Viaflex are trademarks of Baxter International Inc.”
  - baseline: MANUFACTURED_BY → company “Packed by” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PACKAGED_BY → company “Distributed by: Baxter Healthcare Corporation Deerfield” | location “IL 60015 USAPrinted in Ireland CB-30-02-662 Baxter, Mini-Bag Plus, and Viaflex a” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Baxter Healthcare Corporation Deerfield” | location “IL 60015 USAPrinted in Ireland CB-30-02-662 Baxter, Mini-Bag Plus, and Viaflex a” | label-establishment name match: False; DECRS exact-name rows: 0

## S038 · NO_ESTABLISHMENT_BLOCK · `60923-554` ELEVIDYS
- set `3525abcd-fbd2-46c5-9706-cffdf2e8a361` v12 (published 2026-08-17, effective 20260812); labeler ['Sarepta Therapeutics, Inc.']; 61 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v12 (7 versions); sampled version listed: True, published 2026-08-17
- free text (6 hits):
  - [MANUFACTURED_FOR] §42229-5  @3048: “Manufactured for: Sarepta Therapeutics, Inc. Cambridge, MA 02142 USAU.S. license number 2308 SAREPTA, SAREPTA THERAPEUTICS and ELEVIDYS are trademarks of Sarepta Therapeutics, Inc. ©2026 Sarepta Therapeutics, Inc. Elevid”
  - [MANUFACTURED_FOR] §42231-1  @7046: “Manufactured for: Sarepta Therapeutics, Inc. Cambridge, MA 02142 USA U.S. license number 2308SAREPTA, SAREPTA THERAPEUTICS and ELEVIDYS are trademarks of Sarepta Therapeutics, Inc.©2025 Sarepta Therapeutics, Inc.”
  - [MANUFACTURED_FOR] §51945-4  @476: “Manufactured for Sarepta Therapeutics, Inc.,Cambridge, MA 02142 USA US License No. 2308 SAREPTA THERAPEUTICS”
  - [MANUFACTURED_FOR] §51945-4  @476: “Manufactured for Sarepta Therapeutics, Inc.,Cambridge, MA 02142 USA US License No. 2308”
  - [MANUFACTURED_FOR] §51945-4  @476: “Manufactured for Sarepta Therapeutics, Inc.,Cambridge, MA 02142 USA US License No. 2308”
  - [MANUFACTURED_FOR] §51945-4  @235: “Mfg. for: Sarepta Therapeutics, Inc.,Cambridge, MA 02142 USAUS License No. 2308 Rx Only NDC 60923-562-01”
  - baseline: MANUFACTURED_FOR → company “Sarepta Therapeutics” | location “Inc. Cambridge, MA 02142 USAU.S. license number 2308 SAREPTA, SAREPTA THERAPEUTI” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “Sarepta Therapeutics” | location “Inc. Cambridge, MA 02142 USA U.S. license number 2308SAREPTA, SAREPTA THERAPEUTI” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “Sarepta Therapeutics” | location “Inc.,Cambridge, MA 02142 USA US License No. 2308 SAREPTA THERAPEUTICS” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “Sarepta Therapeutics” | location “Inc.,Cambridge, MA 02142 USA US License No. 2308” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “Sarepta Therapeutics” | location “Inc.,Cambridge, MA 02142 USA US License No. 2308” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “Sarepta Therapeutics” | location “Inc.,Cambridge, MA 02142 USAUS License No. 2308 Rx Only NDC 60923-562-01” | label-establishment name match: False; DECRS exact-name rows: 1

## S039 · NO_ESTABLISHMENT_BLOCK · `70518-4174` Cyclobenzaprine Hydrochloride
- set `3175d24d-e8a0-4f14-bed9-a60ad59ac7e7` v3 (published 2026-08-31, effective 20260828); labeler ['REMEDYREPACK INC.']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0093-1921'].
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2026-08-31
- free text (4 hits):
  - [DISTRIBUTED_BY] §34069-5 16.1 How Supplied @533: “Distributed By: Remedy Repack, Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762”
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1902: “Repackaged By /”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1918: “Distributed By: RemedyRepack Inc. 625 Kolter Drive, Indiana, PA 15701 (724) 465-8762”
  - [DISTRIBUTED_BY] §42230-3 Patient Information @8054: “Distributed By: Remedy Repack, Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762 This Patient Information has been approved by the U.S. Food and Drug Administration”
  - baseline: DISTRIBUTED_BY → company “Remedy Repack” | location “Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “/” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “RemedyRepack Inc” | location “625 Kolter Drive, Indiana, PA 15701 (724) 465-8762” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: DISTRIBUTED_BY → company “Remedy Repack” | location “Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762 This Patient Information” | label-establishment name match: False; DECRS exact-name rows: 0

## S040 · NO_ESTABLISHMENT_BLOCK · `42291-785` Progesterone
- set `1637ac18-3a37-f3d5-e063-6394a90af157` v3 (published 2026-05-15, effective 20260513); labeler ['AvKARE']; 2 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2026-05-15
- free text (2 hits):
  - [MANUFACTURED_FOR] §42229-5  @0: “Manufactured for: AvKARE Pulaski, TN 38478 PI-784-00 Rev. 03/2024”
  - [MANUFACTURED_FOR] §42230-3 PATIENT INFORMATION @8715: “Manufactured for: AvKARE Pulaski, TN 38478 PI-784-00 Rev. 03/2024”
  - baseline: MANUFACTURED_FOR → company “AvKARE Pulaski” | location “TN 38478 PI-784-00 Rev. 03/2024” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “AvKARE Pulaski” | location “TN 38478 PI-784-00 Rev. 03/2024” | label-establishment name match: False; DECRS exact-name rows: 0

## S041 · NO_ESTABLISHMENT_BLOCK · `70377-049` Lenalidomide
- set `ed7a3099-ce31-4865-b212-358d9ff6261b` v10 (published 2026-10-14, effective 20250303); labeler ['BIOCON PHARMA INC.,']; 6 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v10 (2 versions); sampled version listed: True, published 2026-10-14
- free text (4 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @6718: “Manufactured by: Biocon Pharma Limited Bengaluru, India – 560099”
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @6783: “Manufactured for: Biocon Pharma Inc., Iselin, New Jersey, 08830-3009 United States of America”
  - [MANUFACTURED_BY] §42231-1  @15991: “Manufactured by: Biocon Pharma Limited Bengaluru, India – 560099”
  - [MANUFACTURED_FOR] §42231-1  @16056: “Manufactured for: Biocon Pharma Inc., Iselin, New Jersey, 08830-3009 United States of America”
  - baseline: MANUFACTURED_BY → company “Biocon Pharma Limited Bengaluru” | location “India – 560099” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Biocon Pharma Inc” | location “, Iselin, New Jersey, 08830-3009 United States of America” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Biocon Pharma Limited Bengaluru” | location “India – 560099” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Biocon Pharma Inc” | location “, Iselin, New Jersey, 08830-3009 United States of America” | label-establishment name match: False; DECRS exact-name rows: 1

## S042 · NO_ESTABLISHMENT_BLOCK · `0049-0354` Geodon
- set `8326928a-2cb6-4f7f-9712-03a425a14c37` v50 (published 2026-09-18, effective 20250113); labeler ['ROERIG']; 12 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v50 (42 versions); sampled version listed: True, published 2026-09-18
- free text (2 hits):
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @3346: “Distributed by: Viatris Specialty LLC Morgantown, WV 26505 U.S.A. © 2024 Viatris Inc. GEODON is a registered trademark of Viatris Specialty LLC, a Viatris Company. The brands listed are trademarks of their respective own”
  - [DISTRIBUTED_BY] §42230-3 PATIENT SUMMARY OF INFORMATION ABOUT @11015: “Distributed by: Viatris Specialty LLC Morgantown, WV 26505 U.S.A. © 2024 Viatris Inc. GEODON is a registered trademark of Viatris Specialty LLC, a Viatris Company. The brands listed are trademarks of their respective own”
  - baseline: DISTRIBUTED_BY → company “Viatris Specialty LLC Morgantown” | location “WV 26505 U.S.A. © 2024 Viatris Inc. GEODON is a registered trademark of Viatris ” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Viatris Specialty LLC Morgantown” | location “WV 26505 U.S.A. © 2024 Viatris Inc. GEODON is a registered trademark of Viatris ” | label-establishment name match: False; DECRS exact-name rows: 0

## S043 · NO_ESTABLISHMENT_BLOCK · `62135-489` Diethylpropion Hydrochloride ER
- set `fdb6e69c-4f8e-42d8-bdda-c99ff3ad7c1e` v2 (published 2024-10-14, effective 20241010); labeler ['Chartwell RX, LLC.']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2024-10-14
- free text (1 hits):
  - [MANUFACTURED_FOR] §34069-5 HOW SUPPLIED @342: “Manufactured for: Chartwell RX, LLC. Congers, NY 10920 L71299”
  - baseline: MANUFACTURED_FOR → company “Chartwell RX” | location “LLC. Congers, NY 10920 L71299” | label-establishment name match: False; DECRS exact-name rows: 0

## S044 · NO_ESTABLISHMENT_BLOCK · `47781-852` Bonsity
- set `2d0c89a2-3849-adf6-007d-aeca21cf417c` v1 (published 2025-06-09, effective 20250601); labeler ['Alvogen Inc.']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2025-06-09
- free text (3 hits):
  - [DISTRIBUTED_BY] §42229-5  @51: “Distributed by: Alvogen, Inc. Morristown, NJ 07960 USA PI852-00”
  - [DISTRIBUTED_BY] §42231-1  @8734: “Distributed by: Alvogen, Inc. Morristown, NJ 07960 USA PL852-00”
  - [DISTRIBUTED_BY] §42229-5 Contact Information @199: “Distributed by: Alvogen, Inc. Morristown, NJ 07960 USA BONSITY® is a registered trademark of Pfenex Inc.”
  - baseline: DISTRIBUTED_BY → company “Alvogen” | location “Inc. Morristown, NJ 07960 USA PI852-00” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Alvogen” | location “Inc. Morristown, NJ 07960 USA PL852-00” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Alvogen” | location “Inc. Morristown, NJ 07960 USA BONSITY® is a registered trademark of Pfenex Inc” | label-establishment name match: False; DECRS exact-name rows: 0

## S045 · NO_ESTABLISHMENT_BLOCK · `27808-091` Dexmethylphenidate Hydrochloride
- set `1f2aa66a-51dc-459c-a765-5364bccd310f` v23 (published 2025-03-31, effective 20240731); labeler ['Cranbury Pharmaceuticals, LLC']; 3 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v23 (11 versions); sampled version listed: True, published 2025-03-31
- free text (2 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @3594: “Manufactured by: Tris Pharma, Inc. Monmouth Junction, NJ 08852 For: Cranbury Pharmaceuticals, LLC Monmouth Junction, NJ 08852 LB8408 Rev. 06 07/2024”
  - [MANUFACTURED_BY] §42231-1 MEDICATION GUIDE @12593: “Manufactured by: Tris Pharma, Inc., Monmouth Junction, NJ 08852 For: Cranbury Pharmaceuticals, LLC, Monmouth Junction, NJ 08852 LB8409 Rev. 06 Dispense with Medication Guide available at: https://www.cranburypharma.com/p”
  - baseline: MANUFACTURED_BY → company “Tris Pharma” | location “Inc. Monmouth Junction, NJ 08852 For: Cranbury Pharmaceuticals, LLC Monmouth Jun” | label-establishment name match: False; DECRS exact-name rows: 2
  - baseline: MANUFACTURED_BY → company “Tris Pharma” | location “Inc., Monmouth Junction, NJ 08852 For: Cranbury Pharmaceuticals, LLC, Monmouth J” | label-establishment name match: False; DECRS exact-name rows: 2

## S046 · NO_ESTABLISHMENT_BLOCK · `70518-4547` Heparin Sodium
- set `a5fab0b1-c472-489c-ba87-2f8e53356173` v1 (published 2026-01-19, effective 20260116); labeler ['REMEDYREPACK INC.']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0641-0400'].
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2026-01-19
- free text (3 hits):
  - [DISTRIBUTED_BY] §34069-5 16 HOW SUPPLIED/STORAGE AND HANDLING @379: “Distributed By: Remedy Repack, Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762”
  - [REPACKAGED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1452: “Repackaged By /”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1468: “Distributed By: RemedyRepack Inc. 625 Kolter Drive, Indiana, PA 15701 (724) 465-8762”
  - baseline: DISTRIBUTED_BY → company “Remedy Repack” | location “Inc. 625 Kolter Dr. Suite #4 Indiana, PA 1-724-465-8762” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “/” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “RemedyRepack Inc” | location “625 Kolter Drive, Indiana, PA 15701 (724) 465-8762” | label-establishment name match: False; DECRS exact-name rows: 1

## S047 · NO_ESTABLISHMENT_BLOCK · `70512-787` Oxaprozin
- set `450f5941-7f10-42fe-e063-6394a90a4803` v1 (published 2025-12-04, effective 20251203); labeler ['SOLA Pharmaceuticals, LLC']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2025-12-04
- free text (3 hits):
  - [MANUFACTURED_FOR] §88436-1 17 PATIENT COUNSELING INFORMATION @3654: “Manufactured for: Sola Pharmaceuticals LLC Baton Rouge, LA 70810”
  - [MANUFACTURED_FOR] §42231-1  @7215: “Manufactured for: Sola Pharmaceuticals, LLC Baton Rouge, LA 70810”
  - [MANUFACTURED_FOR] §42229-5  @122: “Manufactured for: SOLA Pharmaceuticals Baton Rouge, LA 70810”
  - baseline: MANUFACTURED_FOR → company “Sola Pharmaceuticals LLC Baton Rouge” | location “LA 70810” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Sola Pharmaceuticals” | location “LLC Baton Rouge, LA 70810” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_FOR → company “SOLA Pharmaceuticals Baton Rouge” | location “LA 70810” | label-establishment name match: False; DECRS exact-name rows: 0

## S048 · NO_ESTABLISHMENT_BLOCK · `25021-821` methylprednisolone acetate
- set `f98314ea-a4e4-4f78-987b-3e9b45a08bb4` v10 (published 2026-07-15, effective 20250302); labeler ['Sagent Pharmaceuticals']; 2 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v10 (3 versions); sampled version listed: True, published 2026-07-15
- free text (2 hits):
  - [MANUFACTURED_FOR] §44425-7 Storage Conditions @167: “Mfd. for SAGENT PharmaceuticalsSchaumburg, IL 60195 (USA)”
  - [MADE_IN] §44425-7 Storage Conditions @225: “Made in India”
  - baseline: MANUFACTURED_FOR → company “SAGENT PharmaceuticalsSchaumburg” | location “IL 60195 (USA)” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “India” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S049 · NO_ESTABLISHMENT_BLOCK · `69543-455` LACOSAMIDE
- set `01162e2f-967b-4596-8188-c0d9889c3814` v2 (published 2026-01-26, effective 20260123); labeler ['Virtus Pharmaceuticals, LLC']; 1 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2026-01-26
- free text (4 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2786: “Manufactured by: Gland Pharma Limited Hyderabad-502307, India.”
  - [DISTRIBUTED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @2849: “Distributed by: Virtus Pharmaceuticals, LLC Langhorne, PA 19047”
  - [MANUFACTURED_BY] §42231-1  @8549: “Manufactured by: Gland Pharma Limited Hyderabad-502307, India.”
  - [DISTRIBUTED_BY] §42231-1  @8612: “Distributed by: Virtus Pharmaceuticals, LLC Langhorne, PA 19047”
  - baseline: MANUFACTURED_BY → company “Gland Pharma Limited Hyderabad-502307” | location “India” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Virtus Pharmaceuticals” | location “LLC Langhorne, PA 19047” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Gland Pharma Limited Hyderabad-502307” | location “India” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Virtus Pharmaceuticals” | location “LLC Langhorne, PA 19047” | label-establishment name match: False; DECRS exact-name rows: 0

## S050 · NO_ESTABLISHMENT_BLOCK · `0904-7587` Ibuprofen
- set `42b6faf5-ef47-6a7a-e063-6394a90ac409` v2 (published 2026-02-10, effective 20260205); labeler ['Major Pharmaceuticals']; 3 products, 0 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / NO_ESTABLISHMENT_BLOCK.
- establishments: []
- ops for this product: none; MANUFACTURE DUNS: none.
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2026-02-10
- free text (4 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @1039: “Manufactured by: Contract Pharmacal Corp. 165 Oser Avenue Hauppauge, NY 11788 USA Toll Free Number: (800) 231-4670”
  - [DISTRIBUTED_BY] §34069-5 HOW SUPPLIED @1154: “Distributed by: MAJOR® PHARMACEUTICALS Indianapolis, IN 46268 Rev. 08/25”
  - [MANUFACTURED_BY] §42231-1 MEDICATION GUIDE @5374: “Manufactured by: Contract Pharmacal Corp., 165 Oser Avenue, Hauppauge, NY 11788”
  - [DISTRIBUTED_BY] §42231-1 MEDICATION GUIDE @5454: “Distributed by: MAJOR® PHARMACEUTICALS Indianapolis, IN 46268 Rev. 08/25”
  - baseline: MANUFACTURED_BY → company “Contract Pharmacal Corp” | location “165 Oser Avenue Hauppauge, NY 11788 USA Toll Free Number: (800) 231-4670” | label-establishment name match: False; DECRS exact-name rows: 7
  - baseline: DISTRIBUTED_BY → company “MAJOR® PHARMACEUTICALS Indianapolis” | location “IN 46268 Rev. 08/25” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Contract Pharmacal Corp” | location “, 165 Oser Avenue, Hauppauge, NY 11788” | label-establishment name match: False; DECRS exact-name rows: 7
  - baseline: DISTRIBUTED_BY → company “MAJOR® PHARMACEUTICALS Indianapolis” | location “IN 46268 Rev. 08/25” | label-establishment name match: False; DECRS exact-name rows: 0

## S051 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `54868-6305` Clobetasol Propionate
- set `218da851-af52-48e6-bfd5-2e716d0a85f0` v1 (published 2011-09-13, effective 20100604); labeler ['Physicians Total Care, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Physicians Total Care, Inc.', '194123980')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '194123980'), ('C73607', 'relabel', '194123980')]; source NDC (asEquivalentEntity): ['50383-270'].
- identity: 194123980 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2011-09-13
- free text (2 hits):
  - [DISTRIBUTED_BY] §34069-5 HOW SUPPLIED @210: “Distributed by: Hi-Tech Pharmacal Co., Inc. Amityville, NY 11701”
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @275: “Manufactured by: DPT Laboratories Ltd San Antonio, TX 78215 Rev. 270:00 10/09 129160-1009 Additional barcode labeling by: Physicians Total Care, Inc.Tulsa, OK 74146”
  - baseline: DISTRIBUTED_BY → company “Hi-Tech Pharmacal Co” | location “, Inc. Amityville, NY 11701” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “DPT Laboratories Ltd San Antonio” | location “TX 78215 Rev. 270:00 10/09 129160-1009 Additional barcode labeling by: Physician” | label-establishment name match: False; DECRS exact-name rows: 0

## S052 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `49778-001` Oxygen
- set `8abd7c2d-89dd-44ff-8add-a9d92f05baea` v1 (published 2010-07-20, effective 20100219); labeler ['American Welding & Gas']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('American Welding & Gas', '832328061')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '832328061')].
- identity: 832328061 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-07-20
- free text (1 hits):
  - [MANUFACTURED_BY] §51945-4  @1007: “PRODUCED BY AIR LIQUEFACTION RETURN WITH 25 PSIG. TO BE REFILLED BY AN INWELD AUTHORIZED FACILITY ONLY. RETURN WITH 25 PSIG. Pressure: ___________ PSIG at 70°FSize: _______________Contents: ___________ LitersDO NOT REMOV”
  - baseline: MANUFACTURED_BY → company “AIR LIQUEFACTION RETURN WITH 25 PSIG” | location “TO BE REFILLED BY AN INWELD AUTHORIZED FACILITY ONLY. RETURN WITH 25 PSIG. Press” | label-establishment name match: False; DECRS exact-name rows: 0

## S053 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-3275` Mugwort
- set `ff973401-4774-4867-a83b-7125f6356ff5` v1 (published 2009-12-17, effective 20091204); labeler ['Nelco Laboratories, Inc.']; 39 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-17
- free text: no manufacturing-role statement found

## S054 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `68387-545` Naproxen Sodium
- set `0fc2f04c-43a0-4831-b499-369f06a4106a` v1 (published 2010-12-14, effective 20101210); labeler ['Keltman Pharmaceuticals Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Keltman Pharmaceuticals Inc.', '362861077')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '362861077'), ('C73607', 'relabel', '362861077')]; source NDC (asEquivalentEntity): ['53746-194'].
- identity: 362861077 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-12-14
- free text (3 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Amneal Pharmaceuticals of NY Hauppauge, NY 11788”
  - [DISTRIBUTED_BY] §42229-5  @66: “Distributed by: Amneal Pharmaceuticals Glasgow, KY 42141 This Product was”
  - [REPACKAGED_BY] §42229-5  @140: “Repackaged By: Keltman Pharmaceuticals Inc. 1 Lakeland Square, Suite A Flowood, MS 39232 United States”
  - baseline: MANUFACTURED_BY → company “Amneal Pharmaceuticals of NY Hauppauge” | location “NY 11788” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Amneal Pharmaceuticals Glasgow” | location “KY 42141 This Product was” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Keltman Pharmaceuticals Inc” | location “1 Lakeland Square, Suite A Flowood, MS 39232 United States” | label-establishment name match: True; DECRS exact-name rows: 0

## S055 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `54868-6316` Levetiracetam
- set `6ecf5268-7ed3-458e-b281-aec3c51656d7` v1 (published 2011-12-13, effective 20111213); labeler ['Physicians Total Care, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Physicians Total Care, Inc.', '194123980')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '194123980'), ('C73607', 'relabel', '194123980')]; source NDC (asEquivalentEntity): ['0093-7795'].
- identity: 194123980 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2011-12-13
- free text (2 hits):
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @2315: “Manufactured For: TEVA PHARMACEUTICALS USA Sellersville, PA 18960 Rev. A 1/2011”
  - [MANUFACTURED_FOR] §42231-1 MEDICATION GUIDE @9014: “Manufactured For: TEVA PHARMACEUTICALS USA Sellersville, PA 18960 Rev. A 1/2011”
  - baseline: MANUFACTURED_FOR → company “TEVA PHARMACEUTICALS USA Sellersville” | location “PA 18960 Rev. A 1/2011” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “TEVA PHARMACEUTICALS USA Sellersville” | location “PA 18960 Rev. A 1/2011” | label-establishment name match: False; DECRS exact-name rows: 0

## S056 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `66116-436` Tri-Sprintec
- set `cbcb4427-7a99-467c-915f-a8b4c90e2832` v1 (published 2011-11-10, effective 20110803); labeler ['MedVantx, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Blenheim Pharmacal, Inc.', '171434587')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'REPACK', '171434587')]; source NDC (asEquivalentEntity): ['0555-9018'].
- identity: 171434587 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2011-11-10
- free text: no manufacturing-role statement found

## S057 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `76366-002` NITROGEN
- set `d67581a5-1408-47f1-bff5-fc41d61e2892` v1 (published 2012-06-15, effective 20120521); labeler ['Cryo Weld Corporation']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Cryo Weld Corporation', '939219593')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '939219593')].
- identity: 939219593 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2012-06-15
- free text: no manufacturing-role statement found

## S058 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `53808-0408` Glipizide XL
- set `d0b36326-e17d-4fff-aa12-a86f5284669f` v1 (published 2010-06-14, effective 20100602); labeler ['State of Florida DOH Central Pharmacy']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('State of Florida DOH Central Pharmacy', '829348114')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '829348114')]; source NDC (asEquivalentEntity): ['59762-5033'].
- identity: 829348114 STALE_REGISTERED FEI 1036356 (DOH CENTRAL PHARMACY)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-06-14
- free text (1 hits):
  - [REPACKAGED_BY] §42230-3 PATIENT INFORMATION @7729: “Repackaged By: State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee, FL 32304 United States”
  - baseline: REPACKAGED_BY → company “State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee” | location “FL 32304 United States” | label-establishment name match: False; DECRS exact-name rows: 0

## S059 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-1808` Horse Fly
- set `33f34062-9219-458c-bb25-7f469a08cd6d` v1 (published 2009-12-18, effective 20091211); labeler ['Nelco Laboratories, Inc.']; 6 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-18
- free text: no manufacturing-role statement found

## S060 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `57728-0001` Oxygen
- set `dacfcf89-e499-4475-aa7d-5b918c6d0fd3` v1 (published 2010-07-20, effective 20091117); labeler ['Atlantic Medical Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Atlantic Medical Inc.', '020041815')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '020041815')].
- identity: 020041815 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-07-20
- free text: no manufacturing-role statement found

## S061 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `53808-0908` Bupropion Hydrochloride
- set `8e9b33e3-beb8-4970-bba5-78fbde261ce5` v1 (published 2010-08-05, effective 20100519); labeler ['State of Florida DOH Central Pharmacy']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('State of Florida DOH Central Pharmacy', '829348114')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '829348114')]; source NDC (asEquivalentEntity): ['60505-158'].
- identity: 829348114 STALE_REGISTERED FEI 1036356 (DOH CENTRAL PHARMACY)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-08-05
- free text (4 hits):
  - [REPACKAGED_BY] §34069-5 HOW SUPPLIED @576: “Repackaged By: State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee, FL 32304 United States”
  - [MANUFACTURED_BY] §51945-4  @50: “Manufactured by: Mylan) buPROPion Hydrochloride Tablets, USP 75 mg WARNING: Do not use in combination with Zyban®* or any other medicines that contain bupropion hydrochloride. 30 TABLETS (Rx only) Each film-coated tablet”
  - [MANUFACTURED_BY] §51945-4  @51: “Manufactured by: Apotex) buPROPion Hydrochloride Tablets, USP 100 mg WARNING: Do not use in combination with Zyban®* or any other medicines that contain bupropion hydrochloride. 30 TABLETS (Rx only) Each film-coated tabl”
  - [MANUFACTURED_BY] §51945-4  @50: “Manufactured by: Apotex) buPROPion Hydrochloride Tablets, USP 75 mg WARNING: Do not use in combination with Zyban®* or any other medicines that contain bupropion hydrochloride. 30 TABLETS (Rx only) Each film-coated table”
  - baseline: REPACKAGED_BY → company “State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee” | location “FL 32304 United States” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Mylan) buPROPion Hydrochloride Tablets” | location “USP 75 mg WARNING: Do not use in combination with Zyban®* or any other medicines” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Apotex) buPROPion Hydrochloride Tablets” | location “USP 100 mg WARNING: Do not use in combination with Zyban®* or any other medicine” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Apotex) buPROPion Hydrochloride Tablets” | location “USP 75 mg WARNING: Do not use in combination with Zyban®* or any other medicines” | label-establishment name match: False; DECRS exact-name rows: 0

## S062 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-2984` White Pine
- set `6f5116d1-f99d-47ef-be88-dca38bbe97f4` v1 (published 2009-12-18, effective 20091203); labeler ['Nelco Laboratories, Inc.']; 85 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-18
- free text: no manufacturing-role statement found

## S063 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-1220` Halibut
- set `ed374a8c-81d6-4389-b77b-00e5517ada89` v1 (published 2009-12-18, effective 20091210); labeler ['Nelco Laboratories, Inc.']; 22 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-18
- free text: no manufacturing-role statement found

## S064 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-2874` California Valley White Oak
- set `40e787f4-4eef-40de-be33-86ab7b36f0f3` v1 (published 2009-12-18, effective 20091203); labeler ['Nelco Laboratories, Inc.']; 85 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-18
- free text: no manufacturing-role statement found

## S065 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `54868-5604` Retin-A MICRO
- set `78f03983-f636-43c3-90c5-3d5231909b2a` v4 (published 2012-02-15, effective 20120214); labeler ['Physicians Total Care, Inc.']; 4 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Physicians Total Care, Inc.', '194123980')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73607', 'relabel', '194123980')]; source NDC (asEquivalentEntity): ['0062-0204'].
- identity: 194123980 NOT_FOUND
- DailyMed today: latest v4 (3 versions); sampled version listed: True, published 2012-02-15
- free text (4 hits):
  - [MARKETED_BY] §42229-5  @29: “Marketed by: Ortho DermatologicsDivision of Ortho-McNeil-Janssen Pharmaceuticals, Inc.Los Angeles, CA 90045 RETIN-A MICRO® is a registered trademark of Ortho-McNeil Pharmaceutical, Inc.MICROSPONGE® is a registered tradem”
  - [MANUFACTURED_BY] §42229-5  @288: “Manufactured by: Ortho Pharmaceuticala division of Janssen Ortho LLC.Manati, Puerto Rico 00674-0463 © OMJPI 2010 RETIN-A MICRO® (tretinoin gel) microsphere, 0.1% and 0.04% Additional barcode labeling by: Physicians Total”
  - [MARKETED_BY] §42230-3 PATIENT INFORMATION @12162: “Marketed by: Ortho DermatologicsDivision of Ortho-McNeil-Janssen Pharmaceuticals, Inc.Los Angeles, CA 90045 RETIN-A MICRO® is a registered trademark of Ortho-McNeil Pharmaceutical, Inc.MICROSPONGE® is a registered tradem”
  - [MANUFACTURED_BY] §42230-3 PATIENT INFORMATION @12421: “Manufactured by: Ortho Pharmaceutical a division of Janssen Ortho LLC. Manati, Puerto Rico 00674-0463 © OMJPI 2010 735442201560”
  - baseline: MARKETED_BY → company “Ortho DermatologicsDivision of Ortho-McNeil-Janssen Pharmaceuticals” | location “Inc.Los Angeles, CA 90045 RETIN-A MICRO® is a registered trademark of Ortho-McNe” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Ortho Pharmaceuticala division of Janssen Ortho LLC” | location “Manati, Puerto Rico 00674-0463 © OMJPI 2010 RETIN-A MICRO® (tretinoin gel) micro” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MARKETED_BY → company “Ortho DermatologicsDivision of Ortho-McNeil-Janssen Pharmaceuticals” | location “Inc.Los Angeles, CA 90045 RETIN-A MICRO® is a registered trademark of Ortho-McNe” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Ortho Pharmaceutical a division of Janssen Ortho LLC” | location “Manati, Puerto Rico 00674-0463 © OMJPI 2010 735442201560” | label-establishment name match: False; DECRS exact-name rows: 0

## S066 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `53808-0923` Terazosin Hydrochloride
- set `6c26db9b-f16c-4797-b6b1-bc51bf2649b5` v1 (published 2010-08-04, effective 20100602); labeler ['State of Florida DOH Central Pharmacy']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('State of Florida DOH Central Pharmacy', '829348114')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '829348114')]; source NDC (asEquivalentEntity): ['00093-4337'].
- identity: 829348114 STALE_REGISTERED FEI 1036356 (DOH CENTRAL PHARMACY)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-08-04
- free text (2 hits):
  - [DISTRIBUTED_BY] §42229-5  @0: “Distributed by: TEVA North Wales, PA This Product was”
  - [REPACKAGED_BY] §42229-5  @54: “Repackaged By: State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee, FL 32304 United States”
  - baseline: DISTRIBUTED_BY → company “TEVA North Wales” | location “PA This Product was” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee” | location “FL 32304 United States” | label-establishment name match: False; DECRS exact-name rows: 0

## S067 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-2761` Red Maple
- set `9e44c782-6ad1-4e86-b333-e9358cbc5867` v1 (published 2009-12-18, effective 20091203); labeler ['Nelco Laboratories, Inc.']; 85 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-18
- free text: no manufacturing-role statement found

## S068 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `42254-183` Spironolactone
- set `c22b0765-1777-4001-836a-2684daf2a35b` v1 (published 2012-05-11, effective 20120320); labeler ['Rebel Distributors Corp']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Rebel Distributors Corp', '118802834')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'REPACK', '118802834'), ('C73607', 'RELABEL', '118802834')]; source NDC (asEquivalentEntity): ['0228-2803'].
- identity: 118802834 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2012-05-11
- free text (2 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @415: “Manufactured by: Actavis Elizabeth LLC 200 Elmora Avenue, Elizabeth, NJ 07207 USA 40-9048”
  - [REPACKAGED_BY] §34069-5 HOW SUPPLIED @528: “Repackaged by: Rebel Distributors Corp Thousand Oaks, CA 91320”
  - baseline: MANUFACTURED_BY → company “Actavis Elizabeth LLC 200 Elmora Avenue” | location “Elizabeth, NJ 07207 USA 40-9048” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Rebel Distributors Corp Thousand Oaks” | location “CA 91320” | label-establishment name match: False; DECRS exact-name rows: 0

## S069 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `52959-630` Clonazepam
- set `ec0e596c-baca-417d-8aa4-a1878100064d` v1 (published 2011-12-15, effective 20111011); labeler ['H.J. Harkins Company, Inc.']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Actavis Elizabeth LLC', '623114928')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'MANUFACTURE', '623114928')]; source NDC (asEquivalentEntity): ['0228-3004'].
- identity: 623114928 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2011-12-15
- free text (2 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @823: “Manufactured by: Actavis Elizabeth LLC 200 Elmora Avenue Elizabeth, NJ 07207 USA 40-9148”
  - [MANUFACTURED_BY] §42231-1 Medication Guide @9327: “Manufactured by: Actavis Elizabeth LLC 200 Elmora Avenue Elizabeth, NJ 07207 USA MG1010 (MG 41-1164) 40-9148 Repacked by: H.J. Harkins Company, Inc. 513 Sandydale Lane Nipomo, CA 93444 USA”
  - baseline: MANUFACTURED_BY → company “Actavis Elizabeth LLC 200 Elmora Avenue Elizabeth” | location “NJ 07207 USA 40-9148” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Actavis Elizabeth LLC 200 Elmora Avenue Elizabeth” | location “NJ 07207 USA MG1010 (MG 41-1164) 40-9148 Repacked by: H.J. Harkins Company, Inc.” | label-establishment name match: False; DECRS exact-name rows: 0

## S070 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `66414-001` Oxygen
- set `fa610da6-5866-4894-a3f0-922430bfefa7` v2 (published 2010-07-20, effective 20100329); labeler ['Garland Welding Supply Company']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Garland Welding Supply Company', '066660275')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '066660275')].
- identity: 066660275 NOT_FOUND
- DailyMed today: latest v2 (1 versions); sampled version listed: True, published 2010-07-20
- free text: no manufacturing-role statement found

## S071 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-2039` Penicilium chrysogenum
- set `102d5d44-e217-4e5d-a9ac-a242388a5cc9` v1 (published 2010-07-19, effective 20091214); labeler ['Nelco Laboratories, Inc.']; 34 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-07-19
- free text: no manufacturing-role statement found

## S072 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `36987-1851` Aspergillus fumigatus
- set `cd1c8eb7-3b26-4767-b638-b795140a9242` v1 (published 2009-12-18, effective 20091214); labeler ['Nelco Laboratories, Inc.']; 34 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Nelco Laboratories, Inc.', '054980867')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C43360', 'manufacture', '054980867')].
- identity: 054980867 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2009-12-18
- free text: no manufacturing-role statement found

## S073 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `21695-732` Gemfibrozil
- set `d709812f-e958-4065-a447-c2c00ddd7677` v1 (published 2011-03-14, effective 20110308); labeler ['Rebel Distributors Corp']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('Rebel Distributors Corp', '118802834')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'REPACK', '118802834'), ('C73607', 'RELABEL', '118802834')]; source NDC (asEquivalentEntity): ['31722-225'].
- identity: 118802834 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2011-03-14
- free text (2 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @358: “Manufactured By: Camber Pharmaceuticals Piscataway, NJ 08854”
  - [REPACKAGED_BY] §34069-5 HOW SUPPLIED @419: “Repackaged by: Rebel Distributors Corp Thousand Oaks, CA 91320 Original--11/2010--NJW”
  - baseline: MANUFACTURED_BY → company “Camber Pharmaceuticals Piscataway” | location “NJ 08854” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: REPACKAGED_BY → company “Rebel Distributors Corp Thousand Oaks” | location “CA 91320 Original--11/2010--NJW” | label-establishment name match: False; DECRS exact-name rows: 0

## S074 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `53808-0803` Triamterene and Hydrochlorothiazide
- set `1a1ba6bd-e1f4-4928-a32b-a63416ce8681` v1 (published 2010-06-11, effective 20100521); labeler ['State of Florida DOH Central Pharmacy']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('State of Florida DOH Central Pharmacy', '829348114')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '829348114')]; source NDC (asEquivalentEntity): ['0781-2074'].
- identity: 829348114 STALE_REGISTERED FEI 1036356 (DOH CENTRAL PHARMACY)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2010-06-11
- free text (2 hits):
  - [MANUFACTURED_BY] §42229-5  @17: “Manufactured By: Sandoz Inc. Princeton, NJ 08540 And”
  - [REPACKAGED_BY] §42229-5  @70: “Repackaged By: State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee, FL 32304 United States”
  - baseline: MANUFACTURED_BY → company “Sandoz Inc” | location “Princeton, NJ 08540 And” | label-establishment name match: False; DECRS exact-name rows: 4
  - baseline: REPACKAGED_BY → company “State of Florida DOH Central Pharmacy 104-2 Hamilton Park Drive Tallahassee” | location “FL 32304 United States” | label-establishment name match: False; DECRS exact-name rows: 0

## S075 · ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT · `16590-126` IBUPROFEN
- set `9c9541af-3221-4e6c-a1eb-fae64925a488` v4 (published 2012-07-09, effective 20120703); labeler ['STAT RX USA LLC']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT.
- establishments: [('STAT RX USA LLC', '786036330')]
- ops for this product: none; MANUFACTURE DUNS: none; unscoped ops: [('C73606', 'repack', '786036330'), ('C73607', 'relabel', '786036330')]; source NDC (asEquivalentEntity): ['55111-684'].
- identity: 786036330 NOT_FOUND
- DailyMed today: latest v4 (3 versions); sampled version listed: True, published 2012-07-09
- free text (1 hits):
  - [DISTRIBUTED_BY] §34069-5 HOW SUPPLIED @834: “Distributed by: Dr. Reddy’s Laboratories, Inc. Bridgewater, NJ 08807 USA”
  - baseline: DISTRIBUTED_BY → company “Dr” | location “Reddy’s Laboratories, Inc. Bridgewater, NJ 08807 USA” | label-establishment name match: False; DECRS exact-name rows: 0

## S076 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `10544-562` Metronidazole
- set `0ff3b187-4773-1d14-e054-00144ff88e88` v1 (published 2015-02-26, effective 20150225); labeler ['Blenheim Pharmacal, Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Blenheim Pharmacal, Inc.', '171434587')]
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0591-2521'].
- identity: 171434587 NOT_FOUND
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2015-02-26
- free text (2 hits):
  - [MANUFACTURED_BY] §34093-5 REFERENCES @614: “Manufactured by: Watson Pharma Private Limited Verna, Salcette Goa 403 722 INDIA”
  - [DISTRIBUTED_BY] §34093-5 REFERENCES @695: “Distributed by: Actavis Pharma, Inc. Parsippany, NJ 07054 USA”
  - baseline: MANUFACTURED_BY → company “Watson Pharma Private Limited Verna” | location “Salcette Goa 403 722 INDIA” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Actavis Pharma” | location “Inc. Parsippany, NJ 07054 USA” | label-establishment name match: False; DECRS exact-name rows: 0

## S077 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `0990-7730` Sodium Chloride
- set `5f372b75-d7a4-471e-8ac6-290040fc84b0` v14 (published 2025-11-17, effective 20251102); labeler ['ICU Medical Inc.']; 4 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Hospira, Inc.', '093132819')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('0990-7983', '093132819'), ('0990-7985', '093132819')].
- identity: 093132819 CURRENT_REGISTERED FEI 1021343 (Hospira, Inc.)
- DailyMed today: latest v14 (9 versions); sampled version listed: True, published 2025-11-17
- free text (1 hits):
  - [MANUFACTURED_FOR] §51945-4 PRINCIPAL DISPLAY PANEL - 250 mL Bag Label @593: “Manufactured for ICU Medical, Inc.,Lake Forest, Illinois, 60045, USA icumedical”
  - baseline: MANUFACTURED_FOR → company “ICU Medical” | location “Inc.,Lake Forest, Illinois, 60045, USA icumedical” | label-establishment name match: False; DECRS exact-name rows: 0

## S078 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `55045-3729` ONDANSETRON HYDROCHLORIDE
- set `2e57105a-b925-4182-9f70-d0fa0e613051` v2 (published 2013-11-06, effective 20131105); labeler ['Dispensing Solutions, Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Dispensing Solutions, Inc.', '066070785')]
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['62756-130'].
- identity: 066070785 NOT_FOUND
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2013-11-06
- free text (3 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Sun Pharmaceutical Industries Ltd. Acme Plaza, Andheri-Kurla Road, Andheri (East), Mumbai-400 059, India.”
  - [DISTRIBUTED_BY] §42229-5  @123: “Distributed by: CARACO PHARMACEUTICAL LABORATORIES LTD. DETROIT, MI 48202. And”
  - [RELABELED_BY] §42229-5  @202: “Relabeled By: Dispensing Solutions Inc. 3000 West Warner AveSanta Ana, CA 92704United States”
  - baseline: MANUFACTURED_BY → company “Sun Pharmaceutical Industries Ltd” | location “Acme Plaza, Andheri-Kurla Road, Andheri (East), Mumbai-400 059, India” | label-establishment name match: False; DECRS exact-name rows: 12
  - baseline: DISTRIBUTED_BY → company “CARACO PHARMACEUTICAL LABORATORIES LTD” | location “DETROIT, MI 48202. And” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: RELABELED_BY → company “Dispensing Solutions Inc” | location “3000 West Warner AveSanta Ana, CA 92704United States” | label-establishment name match: True; DECRS exact-name rows: 0

## S079 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `40032-082` Amlodipine and Valsartan
- set `f4f7081c-a05c-436f-967b-34060087edda` v5 (published 2015-04-22, effective 20150330); labeler ['Novel Laboratories, Inc.']; 4 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Novel Laboratories, Inc.', '793518643')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('40032-083', '793518643')].
- identity: 793518643 CURRENT_REGISTERED FEI 3006271438 (Novel Laboratories, Inc.)
- DailyMed today: latest v5 (1 versions); sampled version listed: True, published 2015-04-22
- free text (2 hits):
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @444: “Manufactured by: Novel Laboratories Inc. Somerset, NJ 08873 PI0800000102 Rev. 12/2014 FDA-APPROVED PATIENT LABELING PATIENT INFORMATION Amlodipine (am loe' di peen) and Valsartan (val sar' tan) Tablets Read the Patient I”
  - [MANUFACTURED_BY] §42229-5  @7895: “Manufactured by: Novel Laboratories Inc. Somerset, NJ 08873 PI0800000102 Rev. 12/2014”
  - baseline: MANUFACTURED_BY → company “Novel Laboratories Inc” | location “Somerset, NJ 08873 PI0800000102 Rev. 12/2014 FDA-APPROVED PATIENT LABELING PATIE” | label-establishment name match: True; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Novel Laboratories Inc” | location “Somerset, NJ 08873 PI0800000102 Rev. 12/2014” | label-establishment name match: True; DECRS exact-name rows: 1

## S080 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `50458-601` Risperidone M-TAB
- set `701e1cd8-2868-4d29-85a9-a2212c88165f` v35 (published 2026-08-24, effective 20260820); labeler ['Janssen Pharmaceuticals, Inc.']; 11 products, 5 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Janssen Pharmaceutica NV', '400345889'), ('Janssen Ortho LLC', '805887986'), ('Janssen Pharmaceutical Sciences Unlimited Company', '985639841'), ('LUSOMEDICAMENTA - SOCIEDADE TECNICA FARMACEUTICA, S.A.', '450630343'), ('Janssen Pharmaceutica NV', '370005019')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('50458-591', '805887986'), ('50458-592', '805887986'), ('50458-593', '805887986'), ('50458-594', '805887986'), ('50458-595', '805887986'), ('50458-596', '370005019'), ('50458-596', '450630343')].
- identity: 370005019 CURRENT_REGISTERED FEI 3002807336 (Janssen Pharmaceutica NV); 400345889 CURRENT_REGISTERED FEI 3002807337 (Janssen Pharmaceutica NV); 450630343 CURRENT_REGISTERED FEI 3005491771 (LUSOMEDICAMENTA - SOCIEDADE TECNICA FARMACEUTICA, S.A.); 805887986 CURRENT_REGISTERED FEI 3002942061 (Janssen Ortho LLC); 985639841 CURRENT_REGISTERED FEI 3002807361 (Janssen Pharmaceutical Sciences Unlimited Company)
- DailyMed today: latest v35 (33 versions); sampled version listed: True, published 2026-08-24
- free text (7 hits):
  - [MANUFACTURED_FOR] §59845-8 INSTRUCTIONS FOR USE Risperidone Oral Solution @4180: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044,USA This Instructions for Use has been approved by the U.S. Food and Drug Administration.”
  - [PRODUCT_OF] §51945-4  @323: “Product of Ireland”
  - [MANUFACTURED_BY] §51945-4  @342: “Manufactured by: JOLLC Gurabo, Puerto Rico 00778”
  - [MANUFACTURED_FOR] §51945-4  @391: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC”
  - [PRODUCT_OF] §51945-4  @323: “Product of Ireland”
  - [MANUFACTURED_BY] §51945-4  @342: “Manufactured by: JOLLC Gurabo, Puerto Rico 00778”
  - [MANUFACTURED_FOR] §51945-4  @391: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC”
  - baseline: MANUFACTURED_FOR → company “Patriot Pharmaceuticals” | location “LLC Horsham, PA 19044,USA This Instructions for Use has been approved by the U.S” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PRODUCT_OF → company “Ireland” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “JOLLC Gurabo” | location “Puerto Rico 00778” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Patriot Pharmaceuticals” | location “LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PRODUCT_OF → company “Ireland” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “JOLLC Gurabo” | location “Puerto Rico 00778” | label-establishment name match: False; DECRS exact-name rows: 0

## S081 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `10544-068` Metformin Hydrochloride
- set `11319112-6ec5-32e7-e054-00144ff8d46c` v2 (published None, effective 20150313); labeler ['Blenheim Pharmacal, Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Blenheim Pharmacal, Inc.', '171434587')]
- ops for this product: none; MANUFACTURE DUNS: none; source NDC (asEquivalentEntity): ['0093-1048'].
- identity: 171434587 NOT_FOUND
- DailyMed today: latest v2 (1 versions); sampled version listed: True, published 2015-03-16
- free text (2 hits):
  - [MANUFACTURED_FOR] §44425-7 Storage @266: “Manufactured For: TEVA PHARMACEUTICALS USA Sellersville, PA 18960 Rev. AM 9/2009”
  - [MANUFACTURED_FOR] §42230-3 PATIENT INFORMATION ABOUT METFORMIN HYDROCHLORIDE TABLETS USP @9389: “Manufactured For: TEVA PHARMACEUTICALS USA Sellersville, PA 18960 Rev. G 8/2007”
  - baseline: MANUFACTURED_FOR → company “TEVA PHARMACEUTICALS USA Sellersville” | location “PA 18960 Rev. AM 9/2009” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “TEVA PHARMACEUTICALS USA Sellersville” | location “PA 18960 Rev. G 8/2007” | label-establishment name match: False; DECRS exact-name rows: 0

## S082 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `50458-604` Risperidone M-TAB
- set `701e1cd8-2868-4d29-85a9-a2212c88165f` v35 (published 2026-08-24, effective 20260820); labeler ['Janssen Pharmaceuticals, Inc.']; 11 products, 5 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Janssen Pharmaceutica NV', '400345889'), ('Janssen Ortho LLC', '805887986'), ('Janssen Pharmaceutical Sciences Unlimited Company', '985639841'), ('LUSOMEDICAMENTA - SOCIEDADE TECNICA FARMACEUTICA, S.A.', '450630343'), ('Janssen Pharmaceutica NV', '370005019')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('50458-591', '805887986'), ('50458-592', '805887986'), ('50458-593', '805887986'), ('50458-594', '805887986'), ('50458-595', '805887986'), ('50458-596', '370005019'), ('50458-596', '450630343')].
- identity: 370005019 CURRENT_REGISTERED FEI 3002807336 (Janssen Pharmaceutica NV); 400345889 CURRENT_REGISTERED FEI 3002807337 (Janssen Pharmaceutica NV); 450630343 CURRENT_REGISTERED FEI 3005491771 (LUSOMEDICAMENTA - SOCIEDADE TECNICA FARMACEUTICA, S.A.); 805887986 CURRENT_REGISTERED FEI 3002942061 (Janssen Ortho LLC); 985639841 CURRENT_REGISTERED FEI 3002807361 (Janssen Pharmaceutical Sciences Unlimited Company)
- DailyMed today: latest v35 (33 versions); sampled version listed: True, published 2026-08-24
- free text (7 hits):
  - [MANUFACTURED_FOR] §59845-8 INSTRUCTIONS FOR USE Risperidone Oral Solution @4180: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044,USA This Instructions for Use has been approved by the U.S. Food and Drug Administration.”
  - [PRODUCT_OF] §51945-4  @323: “Product of Ireland”
  - [MANUFACTURED_BY] §51945-4  @342: “Manufactured by: JOLLC Gurabo, Puerto Rico 00778”
  - [MANUFACTURED_FOR] §51945-4  @391: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC”
  - [PRODUCT_OF] §51945-4  @323: “Product of Ireland”
  - [MANUFACTURED_BY] §51945-4  @342: “Manufactured by: JOLLC Gurabo, Puerto Rico 00778”
  - [MANUFACTURED_FOR] §51945-4  @391: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC”
  - baseline: MANUFACTURED_FOR → company “Patriot Pharmaceuticals” | location “LLC Horsham, PA 19044,USA This Instructions for Use has been approved by the U.S” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PRODUCT_OF → company “Ireland” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “JOLLC Gurabo” | location “Puerto Rico 00778” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Patriot Pharmaceuticals” | location “LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PRODUCT_OF → company “Ireland” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “JOLLC Gurabo” | location “Puerto Rico 00778” | label-establishment name match: False; DECRS exact-name rows: 0

## S083 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `0941-0429` DIANEAL PD-2 with Dextrose
- set `aa268d3f-7389-4f25-801f-5d4825495f08` v37 (published 2026-04-23, effective 20260416); labeler ['Vantive US Healthcare LLC']; 15 products, 2 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Baxter, S.A. de C.V.', '810432484'), ('VANTIVE MANUFACTURING LIMITED', '986154341')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('0941-0409', '810432484'), ('0941-0411', '810432484'), ('0941-0413', '810432484'), ('0941-0415', '810432484'), ('0941-0457', '810432484'), ('0941-0459', '810432484'), ('0941-0484', '986154341'), ('0941-0487', '986154341'), ('0941-0490', '986154341')].
- identity: 810432484 CURRENT_REGISTERED FEI 0000006898 (Baxter, S.A. de C.V.); 986154341 CURRENT_REGISTERED FEI 0000000405 (VANTIVE MANUFACTURING LIMITED)
- DailyMed today: latest v37 (31 versions); sampled version listed: True, published 2026-04-23
- free text (15 hits):
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @1026: “MADE IN USA PD-2 1.5% Dextrose Bar Code (01)00309410411117 NDC 0941-0413-07 (07-25-00-0677) Container Label L5B5194 5000 mL NDC 0941-0413-07 (APPROX 150 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution w”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @2113: “MADE IN USA PD-2 2.5% Dextrose Bar Code (01) 00309410413074 NDC 0941-0415-06 (07-25-56-591) Container Label L5B5187 2000 mL NDC 0941-0415-06 (APPROX 80 mL EXCESS) 3000 mL NOMINAL SIZE CONTAINER Vantive Logo Dianeal PD-2 ”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @3368: “MADE IN USA PD-2 4.25% Dextrose NDC 0941-0409-07 (07-25-00-0676) Container Label L5B4826 5000 mL NDC 0941-0409-07 (APPROX 150 mL EXCESS) Vantive Logo Dianeal Low Calcium (2.5 mEq/L) Peritoneal Dialysis Solution with 1.5%”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @4447: “MADE IN USA Low Calcium 1.5% Dextrose Bar Code (01)00309410409077 NDC 0941-0457-08 (07-25-00-0739) Container Label L5B9727 2000 mL NDC 0941-0457-08 (APPROX 80 mL EXCESS) 3000 mL NOMINAL SIZE CONTANER Vantive Logo Dianeal”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @5589: “MADE IN USA Low Calcium 2.5% Dextrose Bar Code (01)00309410457085 NDC 0941-0459-08 Container Label L5B9747 2000 mL NDC 0941-0459-08 (APPROX 80 mL EXCESS) 3000 mL NOMINAL SIZE CONTAINER Vantive Logo Dianeal Low Calcium (2”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @6732: “MADE IN USA Low Calcium 4.25% Dextrose NDC 0941-0426-52 Container Label 5B9866 2000 mL NDC 0941-0426-52 (APPROX 80 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution with 1.5% Dextrose EACH 100 mL CONTAINS”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @7777: “MADE IN USA PD-2 1.5% Dextrose NDC 0941-0427-52 Container Label 5B9876 2000 mL NDC 0941-0427-52 (APPROX 80 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution with 2.5% Dextrose EACH 100 mL CONTAINS 2.5 g D”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @8817: “MADE IN USA PD-2 2.5% Dextrose NDC 0941-0429-52 Container Label 5B9896 2000 mL NDC 0941-0429-52 (APPROX 80 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution with 4.25% Dextrose EACH 100 mL CONTAINS 4.25 g”
  - baseline: MADE_IN → company “USA PD-2 1” | location “5% Dextrose Bar Code (01)00309410411117 NDC 0941-0413-07 (07-25-00-0677) Contain” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA PD-2 2” | location “5% Dextrose Bar Code (01) 00309410413074 NDC 0941-0415-06 (07-25-56-591) Contain” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA PD-2 4” | location “25% Dextrose NDC 0941-0409-07 (07-25-00-0676) Container Label L5B4826 5000 mL ND” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA Low Calcium 1” | location “5% Dextrose Bar Code (01)00309410409077 NDC 0941-0457-08 (07-25-00-0739) Contain” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA Low Calcium 2” | location “5% Dextrose Bar Code (01)00309410457085 NDC 0941-0459-08 Container Label L5B9747” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA Low Calcium 4” | location “25% Dextrose NDC 0941-0426-52 Container Label 5B9866 2000 mL NDC 0941-0426-52 (A” | label-establishment name match: False; DECRS exact-name rows: 0

## S084 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `0169-4572` WEGOVY
- set `ee06186f-2aa3-4990-a760-757579d8f77b` v19 (published 2026-06-30, effective 20260618); labeler ['Novo Nordisk Pharmaceutical Industries, LP']; 16 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Novo Nordisk A/S - 25a-B', '309477891')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('0169-4915', '309477891')].
- identity: 309477891 CURRENT_REGISTERED FEI 3003131673 (Novo Nordisk A/S - 25a-B)
- DailyMed today: latest v19 (19 versions); sampled version listed: True, published 2026-06-30
- free text (6 hits):
  - [MARKETED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @5764: “Marketed by: Novo Nordisk Inc., Plainsboro, NJ 08536 For additional information about WEGOVY contact: Novo Nordisk Inc. 800 Scudders Mill Road Plainsboro, NJ 08536 1-833-934-6891 WEGOVY ® and FlexTouch ® are registered t”
  - [MARKETED_BY] §42231-1 Medication Guide @14440: “Marketed by: Novo Nordisk Inc., Plainsboro, NJ 08536 WEGOVY ® and FlexTouch ® are registered trademarks of Novo Nordisk A/S.”
  - [MARKETED_BY] §59845-8 Instructions for Use – Pen @6716: “Marketed by: Novo Nordisk Inc. Plainsboro, NJ 08536 For information about WEGOVY, go to startWegovy.com or contact: Novo Nordisk Inc. 800 Scudders Mill Road Plainsboro, NJ 08536 1-833-Wegovy-1 WEGOVY ® is a registered tr”
  - [MARKETED_BY] §59845-8 Instructions for Use – WEGOVY HD @6915: “Marketed by: Novo Nordisk Inc. Plainsboro, NJ 08536 For information about WEGOVY, go to startWegovy.com or contact: Novo Nordisk Inc. 800 Scudders Mill Road Plainsboro, NJ 08536 1-833-Wegovy-1 Wegovy® is a registered tra”
  - [MARKETED_BY] §59845-8 Instructions for Use – Manual Prefilled Syringe @6448: “Marketed by: Novo Nordisk Inc. Plainsboro, NJ 08536 For information about WEGOVY, contact: Novo Nordisk Inc. 800 Scudders Mill Road Plainsboro, NJ 08536 1-833-Wegovy-1 Wegovy® is a registered trademark of Novo Nordisk A/”
  - [MARKETED_BY] §59845-8 Instructions for Use - FlexTouch @11985: “Marketed by: Novo Nordisk Inc. Plainsboro, NJ 08536 For information about WEGOVY, contact: Novo Nordisk Inc. 800 Scudders Mill Road Plainsboro, NJ 08536 1-833-wegovy-1 (se habla español) © 2026 Novo Nordisk WEGOVY®, Flex”
  - baseline: MARKETED_BY → company “Novo Nordisk Inc” | location “, Plainsboro, NJ 08536 For additional information about WEGOVY contact: Novo Nor” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MARKETED_BY → company “Novo Nordisk Inc” | location “, Plainsboro, NJ 08536 WEGOVY ® and FlexTouch ® are registered trademarks of Nov” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MARKETED_BY → company “Novo Nordisk Inc” | location “Plainsboro, NJ 08536 For information about WEGOVY, go to startWegovy.com or cont” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MARKETED_BY → company “Novo Nordisk Inc” | location “Plainsboro, NJ 08536 For information about WEGOVY, go to startWegovy.com or cont” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MARKETED_BY → company “Novo Nordisk Inc” | location “Plainsboro, NJ 08536 For information about WEGOVY, contact: Novo Nordisk Inc. 80” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MARKETED_BY → company “Novo Nordisk Inc” | location “Plainsboro, NJ 08536 For information about WEGOVY, contact: Novo Nordisk Inc. 80” | label-establishment name match: False; DECRS exact-name rows: 0

## S085 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `0941-0430` DIANEAL Low Calcium with Dextrose
- set `aa268d3f-7389-4f25-801f-5d4825495f08` v37 (published 2026-04-23, effective 20260416); labeler ['Vantive US Healthcare LLC']; 15 products, 2 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Baxter, S.A. de C.V.', '810432484'), ('VANTIVE MANUFACTURING LIMITED', '986154341')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('0941-0409', '810432484'), ('0941-0411', '810432484'), ('0941-0413', '810432484'), ('0941-0415', '810432484'), ('0941-0457', '810432484'), ('0941-0459', '810432484'), ('0941-0484', '986154341'), ('0941-0487', '986154341'), ('0941-0490', '986154341')].
- identity: 810432484 CURRENT_REGISTERED FEI 0000006898 (Baxter, S.A. de C.V.); 986154341 CURRENT_REGISTERED FEI 0000000405 (VANTIVE MANUFACTURING LIMITED)
- DailyMed today: latest v37 (31 versions); sampled version listed: True, published 2026-04-23
- free text (15 hits):
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @1026: “MADE IN USA PD-2 1.5% Dextrose Bar Code (01)00309410411117 NDC 0941-0413-07 (07-25-00-0677) Container Label L5B5194 5000 mL NDC 0941-0413-07 (APPROX 150 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution w”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @2113: “MADE IN USA PD-2 2.5% Dextrose Bar Code (01) 00309410413074 NDC 0941-0415-06 (07-25-56-591) Container Label L5B5187 2000 mL NDC 0941-0415-06 (APPROX 80 mL EXCESS) 3000 mL NOMINAL SIZE CONTAINER Vantive Logo Dianeal PD-2 ”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @3368: “MADE IN USA PD-2 4.25% Dextrose NDC 0941-0409-07 (07-25-00-0676) Container Label L5B4826 5000 mL NDC 0941-0409-07 (APPROX 150 mL EXCESS) Vantive Logo Dianeal Low Calcium (2.5 mEq/L) Peritoneal Dialysis Solution with 1.5%”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @4447: “MADE IN USA Low Calcium 1.5% Dextrose Bar Code (01)00309410409077 NDC 0941-0457-08 (07-25-00-0739) Container Label L5B9727 2000 mL NDC 0941-0457-08 (APPROX 80 mL EXCESS) 3000 mL NOMINAL SIZE CONTANER Vantive Logo Dianeal”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @5589: “MADE IN USA Low Calcium 2.5% Dextrose Bar Code (01)00309410457085 NDC 0941-0459-08 Container Label L5B9747 2000 mL NDC 0941-0459-08 (APPROX 80 mL EXCESS) 3000 mL NOMINAL SIZE CONTAINER Vantive Logo Dianeal Low Calcium (2”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @6732: “MADE IN USA Low Calcium 4.25% Dextrose NDC 0941-0426-52 Container Label 5B9866 2000 mL NDC 0941-0426-52 (APPROX 80 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution with 1.5% Dextrose EACH 100 mL CONTAINS”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @7777: “MADE IN USA PD-2 1.5% Dextrose NDC 0941-0427-52 Container Label 5B9876 2000 mL NDC 0941-0427-52 (APPROX 80 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution with 2.5% Dextrose EACH 100 mL CONTAINS 2.5 g D”
  - [MADE_IN] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @8817: “MADE IN USA PD-2 2.5% Dextrose NDC 0941-0429-52 Container Label 5B9896 2000 mL NDC 0941-0429-52 (APPROX 80 mL EXCESS) Vantive Logo Dianeal PD-2 Peritoneal Dialysis Solution with 4.25% Dextrose EACH 100 mL CONTAINS 4.25 g”
  - baseline: MADE_IN → company “USA PD-2 1” | location “5% Dextrose Bar Code (01)00309410411117 NDC 0941-0413-07 (07-25-00-0677) Contain” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA PD-2 2” | location “5% Dextrose Bar Code (01) 00309410413074 NDC 0941-0415-06 (07-25-56-591) Contain” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA PD-2 4” | location “25% Dextrose NDC 0941-0409-07 (07-25-00-0676) Container Label L5B4826 5000 mL ND” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA Low Calcium 1” | location “5% Dextrose Bar Code (01)00309410409077 NDC 0941-0457-08 (07-25-00-0739) Contain” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA Low Calcium 2” | location “5% Dextrose Bar Code (01)00309410457085 NDC 0941-0459-08 Container Label L5B9747” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “USA Low Calcium 4” | location “25% Dextrose NDC 0941-0426-52 Container Label 5B9866 2000 mL NDC 0941-0426-52 (A” | label-establishment name match: False; DECRS exact-name rows: 0

## S086 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `50458-602` Risperidone M-TAB
- set `701e1cd8-2868-4d29-85a9-a2212c88165f` v35 (published 2026-08-24, effective 20260820); labeler ['Janssen Pharmaceuticals, Inc.']; 11 products, 5 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Janssen Pharmaceutica NV', '400345889'), ('Janssen Ortho LLC', '805887986'), ('Janssen Pharmaceutical Sciences Unlimited Company', '985639841'), ('LUSOMEDICAMENTA - SOCIEDADE TECNICA FARMACEUTICA, S.A.', '450630343'), ('Janssen Pharmaceutica NV', '370005019')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('50458-591', '805887986'), ('50458-592', '805887986'), ('50458-593', '805887986'), ('50458-594', '805887986'), ('50458-595', '805887986'), ('50458-596', '370005019'), ('50458-596', '450630343')].
- identity: 370005019 CURRENT_REGISTERED FEI 3002807336 (Janssen Pharmaceutica NV); 400345889 CURRENT_REGISTERED FEI 3002807337 (Janssen Pharmaceutica NV); 450630343 CURRENT_REGISTERED FEI 3005491771 (LUSOMEDICAMENTA - SOCIEDADE TECNICA FARMACEUTICA, S.A.); 805887986 CURRENT_REGISTERED FEI 3002942061 (Janssen Ortho LLC); 985639841 CURRENT_REGISTERED FEI 3002807361 (Janssen Pharmaceutical Sciences Unlimited Company)
- DailyMed today: latest v35 (33 versions); sampled version listed: True, published 2026-08-24
- free text (7 hits):
  - [MANUFACTURED_FOR] §59845-8 INSTRUCTIONS FOR USE Risperidone Oral Solution @4180: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044,USA This Instructions for Use has been approved by the U.S. Food and Drug Administration.”
  - [PRODUCT_OF] §51945-4  @323: “Product of Ireland”
  - [MANUFACTURED_BY] §51945-4  @342: “Manufactured by: JOLLC Gurabo, Puerto Rico 00778”
  - [MANUFACTURED_FOR] §51945-4  @391: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC”
  - [PRODUCT_OF] §51945-4  @323: “Product of Ireland”
  - [MANUFACTURED_BY] §51945-4  @342: “Manufactured by: JOLLC Gurabo, Puerto Rico 00778”
  - [MANUFACTURED_FOR] §51945-4  @391: “Manufactured for: Patriot Pharmaceuticals, LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC”
  - baseline: MANUFACTURED_FOR → company “Patriot Pharmaceuticals” | location “LLC Horsham, PA 19044,USA This Instructions for Use has been approved by the U.S” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PRODUCT_OF → company “Ireland” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “JOLLC Gurabo” | location “Puerto Rico 00778” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Patriot Pharmaceuticals” | location “LLC Horsham, PA 19044 PATRIOT PHARMACEUTICALS LLC” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: PRODUCT_OF → company “Ireland” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “JOLLC Gurabo” | location “Puerto Rico 00778” | label-establishment name match: False; DECRS exact-name rows: 0

## S087 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `0003-2188` ORENCIA
- set `0836c6ac-ee37-5640-2fed-a3185a0b16eb` v35 (published 2025-11-18, effective 20251113); labeler ['E.R. Squibb & Sons, L.L.C.']; 4 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Patheon Italia S.p.A.', '338336589')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('0003-2187', '338336589')].
- identity: 338336589 CURRENT_REGISTERED FEI 3003065803 (Patheon Italia S.p.A.)
- DailyMed today: latest v35 (35 versions); sampled version listed: True, published 2025-11-18
- free text: no manufacturing-role statement found

## S088 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `68001-337` Lisinopril
- set `34ebeea1-6812-4697-84c4-b2ae4f39e55f` v12 (published 2026-10-09, effective 20261007); labeler ['BluePoint Laboratories']; 7 products, 2 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Lupin Limited', '650759348'), ('LUPIN LIMITED', '863645527')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('68001-332', '650759348'), ('68001-332', '863645527'), ('68001-333', '650759348'), ('68001-333', '863645527'), ('68001-334', '650759348'), ('68001-334', '863645527'), ('68001-335', '650759348'), ('68001-335', '863645527'), ('68001-336', '650759348'), ('68001-336', '863645527'), ('68001-486', '650759348'), ('68001-486', '863645527')].
- identity: 650759348 CURRENT_REGISTERED FEI 3009843207 (LUPIN LIMITED); 863645527 CURRENT_REGISTERED FEI 3007549629 (LUPIN LIMITED)
- DailyMed today: latest v12 (9 versions); sampled version listed: True, published 2026-10-09
- free text (1 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Lupin Limited, INDIA For BluePoint Laboratories Rev: 05/2021”
  - baseline: MANUFACTURED_BY → company “Lupin Limited” | location “INDIA For BluePoint Laboratories Rev: 05/2021” | label-establishment name match: True; DECRS exact-name rows: 12

## S089 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `68180-986` Sertraline Hydrochloride
- set `42120ff8-b353-4632-9ea9-54de9a698724` v28 (published 2026-02-09, effective 20251014); labeler ['Lupin Pharmaceuticals, Inc.']; 6 products, 3 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('LUPIN LIMITED', '862272739'), ('LUPIN LIMITED', '677600414'), ('LUPIN LIMITED', '863645527')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('68180-351', '677600414'), ('68180-351', '862272739'), ('68180-351', '863645527'), ('68180-352', '677600414'), ('68180-352', '862272739'), ('68180-352', '863645527'), ('68180-353', '677600414'), ('68180-353', '862272739'), ('68180-353', '863645527')].
- identity: 677600414 CURRENT_REGISTERED FEI 3004819820 (LUPIN LIMITED); 862272739 CURRENT_REGISTERED FEI 3004995645 (LUPIN LIMITED); 863645527 CURRENT_REGISTERED FEI 3007549629 (LUPIN LIMITED)
- DailyMed today: latest v28 (23 versions); sampled version listed: True, published 2026-02-09
- free text (4 hits):
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @3019: “Manufactured for: Lupin Pharmaceuticals, Inc. Naples, FL 34108 United States”
  - [MADE_IN] §34076-0 17 PATIENT COUNSELING INFORMATION @3096: “MADE IN INDIA”
  - [MANUFACTURED_FOR] §42231-1  @14186: “Manufactured for: Lupin Pharmaceuticals, Inc. Naples, FL 34108 United States”
  - [MADE_IN] §42231-1  @14263: “MADE IN INDIA”
  - baseline: MANUFACTURED_FOR → company “Lupin Pharmaceuticals” | location “Inc. Naples, FL 34108 United States” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “INDIA” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “Lupin Pharmaceuticals” | location “Inc. Naples, FL 34108 United States” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MADE_IN → company “INDIA” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S090 · ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT · `53157-AS3` Nutricel Additive System - AS3
- set `e713f9f1-4208-4ea9-b33f-d758a06346ce` v1 (published 2013-08-15, effective 20130813); labeler ['Haemonetics Manufacturing Inc']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph NO_MANUFACTURE_EVIDENCE / ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT.
- establishments: [('Haemonetics Manufacturing Inc', '078598396')]
- ops for this product: none; MANUFACTURE DUNS: none; MANUFACTURE for other products: [('53157-120', '078598396')].
- identity: 078598396 STALE_REGISTERED FEI 2013342 (Haemonetics Manufacturing, Inc.)
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2013-08-15
- free text (1 hits):
  - [MANUFACTURED_FOR] §34076-0 MANUFACTURER @0: “Manufactured for: Haemonetics Corporation 400 Wood Road Braintree, MA 02184, USA By: Haemonetics Manufacturing Inc 1630 Industrial Park Street Covina, CA 91722, USA Visit us at www.haemonetics.com Phone: 888.489.5938”
  - baseline: MANUFACTURED_FOR → company “Haemonetics Corporation 400 Wood Road Braintree” | location “MA 02184, USA By: Haemonetics Manufacturing Inc 1630 Industrial Park Street Covi” | label-establishment name match: False; DECRS exact-name rows: 0

## S091 · UNKNOWN_SITE · `72934-2084` FLUOCINOLONE ACETONIDE 0.01/ NIACINAMIDE 4
- set `88ca2e1e-c8ce-d58a-e053-2995a90a409f` v1 (published 2019-05-17, effective 20190513); labeler ['Sincerus Florida LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Sincerus Florida LLC', '080105003')]
- ops for this product: [('C43360', 'manufacture', '080105003')]; MANUFACTURE DUNS: ['080105003'].
- identity: 080105003 NOT_FOUND
- graph MANUFACTURE edges: 080105003 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2019-05-17
- free text: no manufacturing-role statement found

## S092 · UNKNOWN_SITE · `50383-419` Ciclopirox
- set `4439cb3d-6825-4558-a981-122ec15f7b05` v8 (published None, effective 20221012); labeler ['Akorn']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Akorn', '117696873')]
- ops for this product: [('C43360', 'MANUFACTURE', '117696873')]; MANUFACTURE DUNS: ['117696873'].
- identity: 117696873 NOT_FOUND
- graph MANUFACTURE edges: 117696873 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v9 (9 versions); sampled version listed: True, published 2022-10-17; NEWER VERSION EXISTS
- free text (2 hits):
  - [DISTRIBUTED_BY] §34093-5 REFERENCES @520: “Distributed by: Akorn Operating Company LLC Gurnee, IL 60031 Rev. 419:04 07/22”
  - [DISTRIBUTED_BY] §42230-3 PATIENT INFORMATION AND INSTRUCTIONS @3894: “Distributed by: Akorn Operating Company LLC Gurnee, IL 60031 Rev. 419:04 07/22”
  - baseline: DISTRIBUTED_BY → company “Akorn Operating Company LLC Gurnee” | location “IL 60031 Rev. 419:04 07/22” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “Akorn Operating Company LLC Gurnee” | location “IL 60031 Rev. 419:04 07/22” | label-establishment name match: False; DECRS exact-name rows: 0

## S093 · UNKNOWN_SITE · `52565-051` Clobetasol Propionate
- set `a84c85fb-05f6-1eb8-444e-c5613766e3e5` v4 (published 2019-09-11, effective 20180417); labeler ['Teligent Pharma, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Teligent Pharma, Inc.', '011036910')]
- ops for this product: [('C43360', 'manufacture', '011036910')]; MANUFACTURE DUNS: ['011036910'].
- identity: 011036910 NOT_FOUND
- graph MANUFACTURE edges: 011036910 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v4 (3 versions); sampled version listed: True, published 2019-09-11
- free text (1 hits):
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @375: “Manufactured by:Teligent Pharma, Inc.Buena, NJ 08310 C101281PI-051-00Rev 07/2019”
  - baseline: MANUFACTURED_BY → company “Teligent Pharma” | location “Inc.Buena, NJ 08310 C101281PI-051-00Rev 07/2019” | label-establishment name match: True; DECRS exact-name rows: 0

## S094 · UNKNOWN_SITE · `50102-100` LYZA
- set `fe2cb3eb-dcd0-470c-8cf0-78fda554b1f7` v13 (published 2021-01-28, effective 20210125); labeler ['Afaxys Pharma LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Mylan Laboratories Limited', '677604150')]
- ops for this product: [('C25391', 'analysis', '677604150'), ('C43360', 'manufacture', '677604150'), ('C84731', 'pack', '677604150'), ('C84732', 'label', '677604150')]; MANUFACTURE DUNS: ['677604150'].
- identity: 677604150 NOT_FOUND
- graph MANUFACTURE edges: 677604150 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v13 (10 versions); sampled version listed: True, published 2021-01-28
- free text (2 hits):
  - [MANUFACTURED_FOR] §42230-3  @14264: “Manufactured for: Afaxys Pharma LLC Charleston, SC 29403, USA.”
  - [MANUFACTURED_BY] §42230-3  @14327: “Manufactured by: Mylan Laboratories Limited 200012302-000”
  - baseline: MANUFACTURED_FOR → company “Afaxys Pharma LLC Charleston” | location “SC 29403, USA” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Mylan Laboratories Limited 200012302-000” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S095 · UNKNOWN_SITE · `13310-101` FIBRICOR
- set `86c49aff-0a4a-46b5-ac6e-26789bf17c9b` v13 (published 2013-03-21, effective 20130319); labeler ['AR Scientific, Inc.']; 2 products, 2 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Mutual Pharmaceutical Company, Inc.', '121735955'), ('Mutual Pharmaceutical Company, Inc.', '831656777')]
- ops for this product: [('C25391', 'ANALYSIS', '121735955'), ('C43360', 'MANUFACTURE', '121735955'), ('C43360', 'MANUFACTURE', '831656777'), ('C84731', 'PACK', '831656777'), ('C84732', 'LABEL', '831656777')]; MANUFACTURE DUNS: ['121735955', '831656777']; MANUFACTURE for other products: [('13310-102', '121735955'), ('13310-102', '831656777')].
- identity: 121735955 NOT_FOUND; 831656777 NOT_FOUND
- graph MANUFACTURE edges: 121735955 UNKNOWN ['identity:NOT_FOUND']; 831656777 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v13 (7 versions); sampled version listed: True, published 2013-03-21
- free text (2 hits):
  - [MANUFACTURED_FOR] §34076-0 17 PATIENT COUNSELING INFORMATION @1212: “Manufactured for: AR SCIENTIFIC, INC. Philadelphia, PA 19124 USA”
  - [MANUFACTURED_BY] §34076-0 17 PATIENT COUNSELING INFORMATION @1277: “Manufactured by: MUTUAL PHARMACEUTICAL COMPANY, INC. Philadelphia, PA 19124 USA Rev 12, March 2013”
  - baseline: MANUFACTURED_FOR → company “AR SCIENTIFIC” | location “INC. Philadelphia, PA 19124 USA” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “MUTUAL PHARMACEUTICAL COMPANY” | location “INC. Philadelphia, PA 19124 USA Rev 12, March 2013” | label-establishment name match: True; DECRS exact-name rows: 0

## S096 · UNKNOWN_SITE · `59714-012` Oxygen
- set `9af2d6f4-ba8f-5da9-e053-2995a90a3dac` v1 (published 2019-12-31, effective 20191018); labeler ['Airway Oxygen, Inc.']; 1 products, 10 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Airway Oxygen, Inc.', '013045228'), ('Airway Oxygen, Inc.', '023266680'), ('Airway Oxygen, Inc.', '034483774'), ('Airway Oxygen, Inc.', '083171962'), ('Airway Oxygen, Inc.', '131426942'), ('Airway Oxygen, Inc.', '137338849'), ('Airway Oxygen, Inc.', '872769971'), ('Airway Oxygen, Inc.', '052495116'), ('Airway Oxygen, Inc.', '075649876'), ('Airway Oxygen, Inc.', '163962301')]
- ops for this product: [('C43360', 'manufacture', '013045228'), ('C43360', 'manufacture', '023266680'), ('C43360', 'manufacture', '034483774'), ('C43360', 'manufacture', '052495116'), ('C43360', 'manufacture', '075649876'), ('C43360', 'manufacture', '083171962'), ('C43360', 'manufacture', '131426942'), ('C43360', 'manufacture', '137338849'), ('C43360', 'manufacture', '163962301'), ('C43360', 'manufacture', '872769971')]; MANUFACTURE DUNS: ['013045228', '023266680', '034483774', '052495116', '075649876', '083171962', '131426942', '137338849', '163962301', '872769971'].
- identity: 013045228 NOT_FOUND; 023266680 NOT_FOUND; 034483774 NOT_FOUND; 052495116 NOT_FOUND; 075649876 NOT_FOUND; 083171962 NOT_FOUND; 131426942 NOT_FOUND; 137338849 NOT_FOUND; 163962301 NOT_FOUND; 872769971 NOT_FOUND
- graph MANUFACTURE edges: 013045228 UNKNOWN ['identity:NOT_FOUND']; 023266680 UNKNOWN ['identity:NOT_FOUND']; 034483774 UNKNOWN ['identity:NOT_FOUND']; 083171962 UNKNOWN ['identity:NOT_FOUND']; 131426942 UNKNOWN ['identity:NOT_FOUND']; 137338849 UNKNOWN ['identity:NOT_FOUND']; 872769971 UNKNOWN ['identity:NOT_FOUND']; 052495116 UNKNOWN ['identity:NOT_FOUND']; 075649876 UNKNOWN ['identity:NOT_FOUND']; 163962301 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2019-12-31
- free text (1 hits):
  - [MANUFACTURED_BY] §51945-4  @785: “Produced by Air Liquefaction M.D.D. Representative: Medical Product Services Borngasse 20 35619 Braunfels, Germany”
  - baseline: MANUFACTURED_BY → company “Air Liquefaction M” | location “D.D. Representative: Medical Product Services Borngasse 20 35619 Braunfels, Germ” | label-establishment name match: False; DECRS exact-name rows: 0

## S097 · UNKNOWN_SITE · `80268-001` Oxygen
- set `ee0e30ff-bbda-42a3-ac20-d14dc52788c8` v3 (published 2021-11-10, effective 20211109); labeler ['Praxair Mexico, S. de R.L. de C.V']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Praxair Mexico, S. de R.L. de C.V', '812505014')]
- ops for this product: [('C43360', 'manufacture', '812505014')]; MANUFACTURE DUNS: ['812505014'].
- identity: 812505014 NOT_FOUND
- graph MANUFACTURE edges: 812505014 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2021-11-10
- free text: no manufacturing-role statement found

## S098 · UNKNOWN_SITE · `71403-102` Minolira Extended Release
- set `523856a4-530b-4a23-a80a-d72ab08e2c08` v4 (published 2022-12-08, effective 20221102); labeler ['EPI Health, Inc']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('EPI Health, Inc.', '080638894')]
- ops for this product: [('C43360', 'MANUFACTURE', '080638894')]; MANUFACTURE DUNS: ['080638894']; MANUFACTURE for other products: [('71403-101', '080638894')].
- identity: 080638894 NOT_FOUND
- graph MANUFACTURE edges: 080638894 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v4 (4 versions); sampled version listed: True, published 2022-12-08
- free text (6 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Dr. Reddy's Laboratories Limited FTO-SEZ-Process-Unit-01Survey No: 57 to 59, 60, 52 & 72 Sector No: 9 to14 & 17 to 20, Devunipalavalasa Village Ranasthalam Mandal Srikakulam District Andhra Pradesh, Indi”
  - [MANUFACTURED_FOR] §42229-5  @222: “Manufactured for: EPI Health, LLC 134 Columbus St. Charleston, SC 29403, USA MIN-PI-0618150073673”
  - [MANUFACTURED_FOR] §42230-3 PATIENT INFORMATION MINOLIRA (min-oh-li'-rah) (minocycline hydrochloride) extended-release tablets @8108: “Manufactured for: EPI Health, LLC 134 Columbus St. Charleston, SC 29403, USA”
  - [MANUFACTURED_BY] §42230-3 PATIENT INFORMATION MINOLIRA (min-oh-li'-rah) (minocycline hydrochloride) extended-release tablets @8185: “Manufactured by: Dr. Reddy's Laboratories Limited FTO-SEZ, Process Unit-01, Devunipalavalasa Village, Srikakulam (District), Andhra Pradesh, India. Pin-:532409 MINOLIRA is a registered trademark of EPI Health, LLC Item N”
  - [MANUFACTURED_FOR] §59845-8 INSTRUCTIONS FOR USE MINOLIRA (min-oh-li'-rah) (minocycline hydrochloride) extended-release tablets @2447: “Manufactured for: EPI Health, LLC 134 Columbus St. Charleston, SC 29403, USA”
  - [MANUFACTURED_BY] §59845-8 INSTRUCTIONS FOR USE MINOLIRA (min-oh-li'-rah) (minocycline hydrochloride) extended-release tablets @2524: “Manufactured by: Dr. Reddy's Laboratories Limited FTO-SEZ, Process Unit-01, Devunipalavalasa Village, Srikakulam (District), Andhra Pradesh, India. Pin-:532409 MINOLIRA is a registered trademark of EPI Health, LLC Item N”
  - baseline: MANUFACTURED_BY → company “Dr” | location “Reddy's Laboratories Limited FTO-SEZ-Process-Unit-01Survey No: 57 to 59, 60, 52 ” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “EPI Health” | location “LLC 134 Columbus St. Charleston, SC 29403, USA MIN-PI-0618150073673” | label-establishment name match: True; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “EPI Health” | location “LLC 134 Columbus St. Charleston, SC 29403, USA” | label-establishment name match: True; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Dr” | location “Reddy's Laboratories Limited FTO-SEZ, Process Unit-01, Devunipalavalasa Village,” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_FOR → company “EPI Health” | location “LLC 134 Columbus St. Charleston, SC 29403, USA” | label-establishment name match: True; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Dr” | location “Reddy's Laboratories Limited FTO-SEZ, Process Unit-01, Devunipalavalasa Village,” | label-establishment name match: False; DECRS exact-name rows: 0

## S099 · UNKNOWN_SITE · `55648-762` Midazolam hydrochloride
- set `19fbdc82-a727-4345-b67e-d0fd620defca` v1 (published 2012-11-19, effective 20121108); labeler ['Wockhardt Limited']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Wockhardt Limited', '676257570')]
- ops for this product: [('C25391', 'ANALYSIS', '676257570'), ('C43360', 'MANUFACTURE', '676257570'), ('C84731', 'PACK', '676257570'), ('C84732', 'LABEL', '676257570')]; MANUFACTURE DUNS: ['676257570']; MANUFACTURE for other products: [('55648-763', '676257570')].
- identity: 676257570 NOT_FOUND
- graph MANUFACTURE edges: 676257570 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2012-11-19
- free text (2 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Wockhardt Limited, H-14/2, MIDC, Waluj, Aurangabad 431136, Maharashtra, India.”
  - [DISTRIBUTED_BY] §42229-5  @96: “Distributed by: Wockhardt USA LLC. 20 Waterview Blvd. Parsippany, NJ 07054 USA.”
  - baseline: MANUFACTURED_BY → company “Wockhardt Limited” | location “H-14/2, MIDC, Waluj, Aurangabad 431136, Maharashtra, India” | label-establishment name match: True; DECRS exact-name rows: 2
  - baseline: DISTRIBUTED_BY → company “Wockhardt USA LLC” | location “20 Waterview Blvd. Parsippany, NJ 07054 USA” | label-establishment name match: True; DECRS exact-name rows: 2

## S100 · UNKNOWN_SITE · `72934-1055` CLINDAMYCIN 1% / SODIUM SULFACETAMIDE MONOHYDRATE 5% / TRETINOIN 0.025%
- set `88017b99-00e7-5476-e053-2a95a90a66a7` v1 (published 2019-05-06, effective 20190503); labeler ['Sincerus Florida, LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Sincerus Florida, LLC', '080105003')]
- ops for this product: [('C43360', 'manufacture', '080105003')]; MANUFACTURE DUNS: ['080105003'].
- identity: 080105003 NOT_FOUND
- graph MANUFACTURE edges: 080105003 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2019-05-06
- free text: no manufacturing-role statement found

## S101 · UNKNOWN_SITE · `72934-2160` NIACINAMIDE 4% / TAZAROTENE 0.05%
- set `8738b466-967f-687a-e053-2a91aa0a2c1f` v1 (published 2019-05-01, effective 20190423); labeler ['Sincerus Florida, LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Sincerus Florida, LLC', '080105003')]
- ops for this product: [('C43360', 'manufacture', '080105003')]; MANUFACTURE DUNS: ['080105003'].
- identity: 080105003 NOT_FOUND
- graph MANUFACTURE edges: 080105003 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2019-05-01
- free text: no manufacturing-role statement found

## S102 · UNKNOWN_SITE · `72934-2046` CIMETIDINE 10% / LIDOCAINE 5% / SALICYLIC ACID 40%
- set `874cd0d1-8711-225c-e053-2995a90af24b` v1 (published 2019-05-01, effective 20190424); labeler ['Sincerus Florida, LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Sincerus Florida, LLC', '080105003')]
- ops for this product: [('C43360', 'manufacture', '080105003')]; MANUFACTURE DUNS: ['080105003'].
- identity: 080105003 NOT_FOUND
- graph MANUFACTURE edges: 080105003 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2019-05-01
- free text: no manufacturing-role statement found

## S103 · UNKNOWN_SITE · `15408-002` Nitrogen
- set `102134cf-db0e-4996-ac06-e004bc019873` v1 (published 2013-07-24, effective 20130723); labeler ['Westair Gas & Equipment, LLC']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('Westair Gas & Equipment, LP', '020774605')]
- ops for this product: [('C43360', 'manufacture', '020774605')]; MANUFACTURE DUNS: ['020774605'].
- identity: 020774605 NOT_FOUND
- graph MANUFACTURE edges: 020774605 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2013-07-24
- free text (3 hits):
  - [DISTRIBUTED_BY] §51945-4  @1333: “DISTRIBUTED BY PRAXAIR, INC, DANBURY, CT 06810-5113”
  - [MANUFACTURED_BY] §51945-4  @1647: “PRODUCED BY AIR LIQUEFACTION IN CASE OF EMERGENCY:”
  - [DISTRIBUTED_BY] §51945-4  @1938: “DISTRIBUTED BY PRAXAIR, INC, DANBURY, CT 06810-5113”
  - baseline: DISTRIBUTED_BY → company “PRAXAIR” | location “INC, DANBURY, CT 06810-5113” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “AIR LIQUEFACTION IN CASE OF EMERGENCY” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: DISTRIBUTED_BY → company “PRAXAIR” | location “INC, DANBURY, CT 06810-5113” | label-establishment name match: False; DECRS exact-name rows: 0

## S104 · UNKNOWN_SITE · `42195-270` TaperDex 7-day
- set `2eeb2754-4c81-444a-a12c-56767fdbe721` v6 (published 2022-01-19, effective 20220118); labeler ['Xspire Pharma, Llc']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('XSPIRE PHARMA', '078312042')]
- ops for this product: [('C43360', 'manufacture', '078312042')]; MANUFACTURE DUNS: ['078312042']; MANUFACTURE for other products: [('42195-127', '078312042')].
- identity: 078312042 NOT_FOUND
- graph MANUFACTURE edges: 078312042 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v6 (4 versions); sampled version listed: True, published 2022-01-19
- free text (1 hits):
  - [MANUFACTURED_FOR] §34069-5 HOW SUPPLIED @699: “Manufactured for: Xspire Pharma Ridgeland, MS 39157 Rev. 02/2020”
  - baseline: MANUFACTURED_FOR → company “Xspire Pharma Ridgeland” | location “MS 39157 Rev. 02/2020” | label-establishment name match: False; DECRS exact-name rows: 0

## S105 · UNKNOWN_SITE · `72731-123` Oxygen
- set `7be7dbbc-1d75-9bff-e053-2991aa0ad815` v2 (published 2019-11-08, effective 20191107); labeler ['North Coast Home Care, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph UNKNOWN_SITE / EXPLICIT_MANUFACTURE.
- establishments: [('North Coast Home Care, Inc.', '148141526')]
- ops for this product: [('C43360', 'manufacture', '148141526')]; MANUFACTURE DUNS: ['148141526'].
- identity: 148141526 NOT_FOUND
- graph MANUFACTURE edges: 148141526 UNKNOWN ['identity:NOT_FOUND']
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2019-11-08
- free text (1 hits):
  - [MANUFACTURED_BY] §51945-4 Principal for Oxygen Product @1304: “Produced by Air Liquefaction.”
  - baseline: MANUFACTURED_BY → company “Air Liquefaction” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S106 · TENTATIVE · `64091-0001` Oxygen
- set `6a772eeb-1707-49ad-be00-1da24fb5494b` v9 (published 2025-02-10, effective 20250207); labeler ['ProCare Healing Centers, LLP dba Ciara Medical Equipment']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('ProCare Healing Centers, LLP dba Ciara Medical Equipment', '194111014')]
- ops for this product: [('C43360', 'manufacture', '194111014')]; MANUFACTURE DUNS: ['194111014'].
- identity: 194111014 STALE_REGISTERED FEI 3010163198 (ProCare Healing Centers, LLP dba Ciara Medical Equipment)
- graph MANUFACTURE edges: 194111014 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v9 (8 versions); sampled version listed: True, published 2025-02-10
- free text (1 hits):
  - [MANUFACTURED_BY] §51945-4 Principal for Oxygen Product @1304: “Produced by Air Liquefaction.”
  - baseline: MANUFACTURED_BY → company “Air Liquefaction” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S107 · TENTATIVE · `29033-045` Venlafaxine Hydrochloride
- set `b84c7126-9216-4f35-ace4-156a493e2b2d` v5 (published 2021-06-10, effective 20180101); labeler ['Nostrum Laboratories, Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('Nostrum Laboratories, Inc.', '791142354')]
- ops for this product: [('C25391', 'ANALYSIS', '791142354'), ('C43360', 'MANUFACTURE', '791142354'), ('C84731', 'pack', '791142354'), ('C84732', 'label', '791142354')]; MANUFACTURE DUNS: ['791142354']; MANUFACTURE for other products: [('29033-046', '791142354')].
- identity: 791142354 STALE_REGISTERED FEI 1930436 (Nostrum Laboratories, Inc.)
- graph MANUFACTURE edges: 791142354 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v5 (5 versions); sampled version listed: True, published 2021-06-10
- free text (2 hits):
  - [MANUFACTURED_BY] §42229-5  @0: “Manufactured by: Nostrum Laboratories, Inc. Kansas City, MO 64120 Rev: 03 January 2018”
  - [MANUFACTURED_BY] §42231-1 FDA-approved Medication Guide @4465: “Manufactured by: Nostrum Laboratories, Inc. Kansas City, MO 64120 Rev. 00 August 2015”
  - baseline: MANUFACTURED_BY → company “Nostrum Laboratories” | location “Inc. Kansas City, MO 64120 Rev: 03 January 2018” | label-establishment name match: True; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “Nostrum Laboratories” | location “Inc. Kansas City, MO 64120 Rev. 00 August 2015” | label-establishment name match: True; DECRS exact-name rows: 0

## S108 · TENTATIVE · `52374-016` Nitrogen
- set `a64bb3c9-3947-d2f3-a219-24b58ec41abc` v16 (published 2025-11-19, effective 20251118); labeler ['Messer Gas Puerto Rico, Inc']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('Messer Gas Puerto Rico, Inc', '833254548')]
- ops for this product: [('C43360', 'manufacture', '833254548'), ('C82401', 'api manufacture', '833254548')]; MANUFACTURE DUNS: ['833254548']; API DUNS: ['833254548'].
- identity: 833254548 CURRENT_REGISTERED FEI 3004392247 (Messer Gas Puerto Rico Inc)
- graph MANUFACTURE edges: 833254548 TENTATIVE ['identity:fei_changed_across_snapshots']
- DailyMed today: latest v16 (14 versions); sampled version listed: True, published 2025-11-19
- free text: no manufacturing-role statement found

## S109 · TENTATIVE · `0941-0692` DIANEAL LOW CALCIUM WITH DEXTROSE
- set `b0f2c9a2-d9d4-4907-a324-e7a26d489f44` v4 (published 2025-05-12, effective 20250509); labeler ['Vantive US Healthcare LLC']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('Baxter Healthcare (Guangzhou) Co., Ltd', '421040114')]
- ops for this product: [('C25391', 'analysis', '421040114'), ('C43360', 'manufacture', '421040114'), ('C84382', 'sterilize', '421040114'), ('C84731', 'pack', '421040114'), ('C84732', 'label', '421040114')]; MANUFACTURE DUNS: ['421040114']; MANUFACTURE for other products: [('0941-0684', '421040114'), ('0941-0688', '421040114')].
- identity: 421040114 STALE_REGISTERED FEI 3012476520 (Baxter Healthcare (Guangzhou) Co., Ltd)
- graph MANUFACTURE edges: 421040114 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v4 (3 versions); sampled version listed: True, published 2025-05-12
- free text (3 hits):
  - [MANUFACTURED_BY] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @917: “MANUFACTURED BY BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WORLD TRADE INC USA) HK-62710 DIRECTIONSTO BE USED AS DIRECTED BY THE PHYSICIAN Prescription Drug”
  - [MANUFACTURED_BY] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @2240: “MANUFACTURED BY BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WORLD TRADE INC USA) HK-62709 DIRECTIONSTO BE USED AS DIRECTED BY THE PHYSICIAN Prescription Drug”
  - [MANUFACTURED_BY] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @3704: “MANUFACTURED BY BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WORLD TRADE INC USA) HK-62711 DIRECTIONSTO BE USED AS DIRECTED BY THE PHYSICIAN Prescription Drug”
  - baseline: MANUFACTURED_BY → company “BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WOR” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WOR” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WOR” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S110 · TENTATIVE · `68180-898` WYMZYA FE
- set `f9cfdf35-7cd0-4984-99e4-0e4a7df91b4e` v1 (published 2012-12-21, effective 20121219); labeler ['Lupin Pharmaceuticals, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('Warner Chilcott Company, LLC', '152356536')]
- ops for this product: [('C43360', 'MANUFACTURE', '152356536')]; MANUFACTURE DUNS: ['152356536'].
- identity: 152356536 STALE_REGISTERED FEI 2619635 (Teva Puerto Rico LLC)
- graph MANUFACTURE edges: 152356536 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2012-12-21
- free text (1 hits):
  - [MANUFACTURED_BY] §42229-5  @5642: “Manufactured by: Warner Chilcott Company, LLCFajardo, PR 00738Manufactured for: Lupin Pharmaceuticals, Inc.Baltimore, Maryland 21202United States To report SUSPECTED ADVERSE REACTIONS, contact Warner Chilcott at 1-800-52”
  - baseline: MANUFACTURED_BY → company “Warner Chilcott Company” | location “LLCFajardo, PR 00738Manufactured for: Lupin Pharmaceuticals, Inc.Baltimore, Mary” | label-establishment name match: True; DECRS exact-name rows: 0

## S111 · TENTATIVE · `49967-704` Garnier Ombrelle SPF 60 UVA UVB Kids Wet N Protect Sunscreen Protection Even on Wet Skin Hypoallergenic Water/sweat resistant 80 minutes Quick Absorption
- set `e1f4208b-3f24-4e01-b53f-c1778ea5c1b3` v6 (published 2026-01-09, effective 20260107); labeler ["L'Oreal USA Products Inc"]; 1 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [("L'OREAL USA PRODUCTS, INC.", '624244349')]
- ops for this product: [('C43360', 'manufacture', '624244349')]; MANUFACTURE DUNS: ['624244349'].
- identity: 624244349 CURRENT_REGISTERED FEI 1000122130 (L'OREAL USA PRODUCTS, INC.)
- graph MANUFACTURE edges: 624244349 TENTATIVE ['identity:fei_changed_across_snapshots']
- DailyMed today: latest v6 (6 versions); sampled version listed: True, published 2026-01-09
- free text: no manufacturing-role statement found

## S112 · TENTATIVE · `53157-726` Leukotrap WB System - CP2D
- set `1ea3c63e-2125-db28-e063-6394a90a4faf` v2 (published 2025-01-06, effective 20250102); labeler ['Haemonetics Manufacturing Inc']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('Haemonetics Manufacturing Inc', '078598396')]
- ops for this product: [('C43360', 'manufacture', '078598396'), ('C84732', 'label', '078598396')]; MANUFACTURE DUNS: ['078598396'].
- identity: 078598396 STALE_REGISTERED FEI 2013342 (Haemonetics Manufacturing, Inc.)
- graph MANUFACTURE edges: 078598396 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2025-01-06
- free text (1 hits):
  - [MANUFACTURED_FOR] §34076-0 MANUFACTURER @0: “Manufactured for: Haemonetics Corporation 400 Wood Road Braintree, MA 02184, USA By: Haemonetics Manufacturing Inc 1630 Industrial Park Street Covina, CA 91722, USA Visit us at www.haemonetics.com Phone: 888.489.5938”
  - baseline: MANUFACTURED_FOR → company “Haemonetics Corporation 400 Wood Road Braintree” | location “MA 02184, USA By: Haemonetics Manufacturing Inc 1630 Industrial Park Street Covi” | label-establishment name match: False; DECRS exact-name rows: 0

## S113 · TENTATIVE · `68877-003` Nitrogen
- set `b31e2b40-dadc-47a2-ad9c-c2faad9ec2d7` v7 (published None, effective 20241120); labeler ['United States Cylinder Gas Corporation']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('United States Cylinder Gas Corporation', '825010051')]
- ops for this product: [('C43360', 'manufacture', '825010051')]; MANUFACTURE DUNS: ['825010051'].
- identity: 825010051 STALE_REGISTERED FEI 3004642161 (United States Cylinder Gas Corporation)
- graph MANUFACTURE edges: 825010051 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v9 (9 versions); sampled version listed: True, published 2024-11-22; NEWER VERSION EXISTS
- free text: no manufacturing-role statement found

## S114 · TENTATIVE · `0941-0688` DIANEAL LOW CALCIUM WITH DEXTROSE
- set `b0f2c9a2-d9d4-4907-a324-e7a26d489f44` v4 (published 2025-05-12, effective 20250509); labeler ['Vantive US Healthcare LLC']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('Baxter Healthcare (Guangzhou) Co., Ltd', '421040114')]
- ops for this product: [('C25391', 'analysis', '421040114'), ('C43360', 'manufacture', '421040114'), ('C84382', 'sterilize', '421040114'), ('C84731', 'pack', '421040114'), ('C84732', 'label', '421040114')]; MANUFACTURE DUNS: ['421040114']; MANUFACTURE for other products: [('0941-0684', '421040114'), ('0941-0692', '421040114')].
- identity: 421040114 STALE_REGISTERED FEI 3012476520 (Baxter Healthcare (Guangzhou) Co., Ltd)
- graph MANUFACTURE edges: 421040114 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v4 (3 versions); sampled version listed: True, published 2025-05-12
- free text (3 hits):
  - [MANUFACTURED_BY] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @917: “MANUFACTURED BY BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WORLD TRADE INC USA) HK-62710 DIRECTIONSTO BE USED AS DIRECTED BY THE PHYSICIAN Prescription Drug”
  - [MANUFACTURED_BY] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @2240: “MANUFACTURED BY BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WORLD TRADE INC USA) HK-62709 DIRECTIONSTO BE USED AS DIRECTED BY THE PHYSICIAN Prescription Drug”
  - [MANUFACTURED_BY] §51945-4 PACKAGE/LABEL PRINCIPAL DISPLAY PANEL @3704: “MANUFACTURED BY BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WORLD TRADE INC USA) HK-62711 DIRECTIONSTO BE USED AS DIRECTED BY THE PHYSICIAN Prescription Drug”
  - baseline: MANUFACTURED_BY → company “BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WOR” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WOR” | location “” | label-establishment name match: False; DECRS exact-name rows: 0
  - baseline: MANUFACTURED_BY → company “BAXTER HEALTHCARE (GUANGZHOU) CO LTD GUANGZHOU CHINA (AN AFFILIATE OF BAXTER WOR” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S115 · TENTATIVE · `76519-1172` CEFDINIR
- set `7640dd80-1a56-9805-e053-2991aa0acbb5` v1 (published 2018-09-21, effective 20180919); labeler ['H.J. Harkins Company, Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph TENTATIVE / EXPLICIT_MANUFACTURE.
- establishments: [('H.J. Harkins Company, Inc.', '147681894')]
- ops for this product: [('C43360', 'manufacture', '147681894'), ('C73606', 'repack', '147681894'), ('C73607', 'relabel', '147681894')]; MANUFACTURE DUNS: ['147681894']; MANUFACTURE for other products: [('76519-1214', '147681894')].
- identity: 147681894 STALE_REGISTERED FEI 7700044472 (H.J. Harkins Company Inc. dba Pharma Pac)
- graph MANUFACTURE edges: 147681894 TENTATIVE ['identity:STALE_REGISTERED']
- DailyMed today: latest v1 (1 versions); sampled version listed: True, published 2018-09-21
- free text: no manufacturing-role statement found

## S116 · DIRECT · `16729-421` Tacrolimus
- set `80e6817a-9b1e-4f0f-e053-2a91aa0a3d15` v5 (published 2024-10-07, effective 20241004); labeler ['Accord Healthcare Inc.']; 2 products, 1 establishments (0 with FEI id, 0 with address); graph DIRECT / EXPLICIT_MANUFACTURE.
- establishments: [('Intas Pharmaceuticals Limited', '725927649')]
- ops for this product: [('C25391', 'analysis', '725927649'), ('C43360', 'manufacture', '725927649')]; MANUFACTURE DUNS: ['725927649']; MANUFACTURE for other products: [('16729-422', '725927649')].
- identity: 725927649 CURRENT_REGISTERED FEI 3003157498 (Intas Pharmaceuticals Limited)
- graph MANUFACTURE edges: 725927649 DIRECT []
- DailyMed today: latest v5 (4 versions); sampled version listed: True, published 2024-10-07
- free text (4 hits):
  - [MANUFACTURED_FOR] §34069-5 HOW SUPPLIED @396: “Manufactured for: Accord Healthcare, Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA.”
  - [MANUFACTURED_BY] §34069-5 HOW SUPPLIED @501: “Manufactured by: Intas Pharmaceuticals Limited, Plot No.:457/458-Matoda/ Plot No.191/218P-Chacharwadi, Sarkhej-Bavla Highway, Taluka - Sanand, Matoda, Ahmedabad, Gujarat 382210, India. 10 2400 2 6031391”
  - [MANUFACTURED_FOR] §42231-1 MEDICATION GUIDE @7656: “Manufactured for: Accord Healthcare, Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA.”
  - [MANUFACTURED_BY] §42231-1 MEDICATION GUIDE @7761: “Manufactured by: Intas Pharmaceuticals Limited, Plot No.:457/458-Matoda/ Plot No.191/218P-Chacharwadi, Sarkhej-Bavla Highway, Taluka - Sanand, Matoda, Ahmedabad, Gujarat 382210, India. 10 2400 2 6031391”
  - baseline: MANUFACTURED_FOR → company “Accord Healthcare” | location “Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Intas Pharmaceuticals Limited” | location “Plot No.:457/458-Matoda/ Plot No.191/218P-Chacharwadi, Sarkhej-Bavla Highway, Ta” | label-establishment name match: True; DECRS exact-name rows: 6
  - baseline: MANUFACTURED_FOR → company “Accord Healthcare” | location “Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Intas Pharmaceuticals Limited” | location “Plot No.:457/458-Matoda/ Plot No.191/218P-Chacharwadi, Sarkhej-Bavla Highway, Ta” | label-establishment name match: True; DECRS exact-name rows: 6

## S117 · DIRECT · `70954-662` Ketoconazole
- set `00c1cac8-a865-4583-aaba-3a0f21fb31e6` v2 (published 2026-02-06, effective 20260129); labeler ['ANI Pharmaceuticals, Inc.']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph DIRECT / EXPLICIT_MANUFACTURE.
- establishments: [('Novitium Pharma LLC', '080301870')]
- ops for this product: [('C25391', 'ANALYSIS', '080301870'), ('C43360', 'MANUFACTURE', '080301870'), ('C84731', 'PACK', '080301870'), ('C84732', 'LABEL', '080301870')]; MANUFACTURE DUNS: ['080301870'].
- identity: 080301870 CURRENT_REGISTERED FEI 3012541241 (Novitium Pharma LLC)
- graph MANUFACTURE edges: 080301870 DIRECT []
- DailyMed today: latest v2 (2 versions); sampled version listed: True, published 2026-02-06
- free text (1 hits):
  - [DISTRIBUTED_BY] §34069-5 HOW SUPPLIED @365: “Distributed by: ANI Pharmaceuticals, Inc. Baudette, MN 56623”
  - baseline: DISTRIBUTED_BY → company “ANI Pharmaceuticals” | location “Inc. Baudette, MN 56623” | label-establishment name match: False; DECRS exact-name rows: 3

## S118 · DIRECT · `16729-042` Tacrolimus
- set `bd447ffa-9196-4c3c-accf-5adf29b84665` v16 (published 2025-05-29, effective 20250602); labeler ['Accord Healthcare Inc.']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph DIRECT / EXPLICIT_MANUFACTURE.
- establishments: [('Intas Pharmaceuticals Limited', '725927649')]
- ops for this product: [('C25391', 'analysis', '725927649'), ('C43360', 'manufacture', '725927649')]; MANUFACTURE DUNS: ['725927649']; MANUFACTURE for other products: [('16729-041', '725927649'), ('16729-043', '725927649')].
- identity: 725927649 CURRENT_REGISTERED FEI 3003157498 (Intas Pharmaceuticals Limited)
- graph MANUFACTURE edges: 725927649 DIRECT []
- DailyMed today: latest v16 (16 versions); sampled version listed: True, published 2025-05-29
- free text (4 hits):
  - [MANUFACTURED_FOR] §42229-5 17.13 Immunizations @178: “Manufactured For: Accord Healthcare, Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA.”
  - [MANUFACTURED_BY] §42229-5 17.13 Immunizations @283: “Manufactured By: Intas Pharmaceuticals Limited, Plot No : 457, 458, Village – Matoda, Bavla Road, Ta.- Sanand,”
  - [MANUFACTURED_FOR] §42230-3  @12064: “Manufactured For: Accord Healthcare, Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA.”
  - [MANUFACTURED_BY] §42230-3  @12169: “Manufactured By: Intas Pharmaceuticals Limited, Plot No : 457, 458, Village – Matoda, Bavla Road, Ta.- Sanand,”
  - baseline: MANUFACTURED_FOR → company “Accord Healthcare” | location “Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Intas Pharmaceuticals Limited” | location “Plot No : 457, 458, Village – Matoda, Bavla Road, Ta.- Sanand” | label-establishment name match: True; DECRS exact-name rows: 6
  - baseline: MANUFACTURED_FOR → company “Accord Healthcare” | location “Inc., 8041 Arco Corporate Drive, Suite 200, Raleigh, NC 27617, USA” | label-establishment name match: False; DECRS exact-name rows: 1
  - baseline: MANUFACTURED_BY → company “Intas Pharmaceuticals Limited” | location “Plot No : 457, 458, Village – Matoda, Bavla Road, Ta.- Sanand” | label-establishment name match: True; DECRS exact-name rows: 6

## S119 · DIRECT · `0487-4301` Sodium Chloride
- set `a4edf2d5-a9ff-30d4-e053-2995a90a5650` v3 (published 2026-01-28, effective 20260126); labeler ['Nephron Pharmaceuticals Corporation']; 1 products, 1 establishments (0 with FEI id, 0 with address); graph DIRECT / EXPLICIT_MANUFACTURE.
- establishments: [('Nephron SC, LLC', '079160190')]
- ops for this product: [('C25391', 'analysis', '079160190'), ('C43360', 'manufacture', '079160190')]; MANUFACTURE DUNS: ['079160190'].
- identity: 079160190 CURRENT_REGISTERED FEI 3010892830 (Nephron SC, LLC)
- graph MANUFACTURE edges: 079160190 DIRECT []
- DailyMed today: latest v3 (3 versions); sampled version listed: True, published 2026-01-28
- free text (1 hits):
  - [MANUFACTURED_BY] §42229-5  @21: “Manufactured by: Nephron Pharmaceuticals Corporation (Company Logo) Nephron Pharmaceuticals Corporation 4500 12th Street Extension West Columbia, SC 29172 1-844-224-2225”
  - baseline: MANUFACTURED_BY → company “Nephron Pharmaceuticals Corporation (Company Logo) Nephron Pharmaceuticals Corpo” | location “” | label-establishment name match: False; DECRS exact-name rows: 0

## S120 · DIRECT · `70069-653` Brimonidine Tartrate and Timolol Maleate
- set `e4fdbd17-73b7-49ed-9de3-591f36e0645d` v3 (published 2024-10-16, effective 20241014); labeler ['Somerset Therapeutics, LLC']; 3 products, 1 establishments (0 with FEI id, 0 with address); graph DIRECT / EXPLICIT_MANUFACTURE.
- establishments: [('Somerset Therapeutics Private Limited', '677236695')]
- ops for this product: [('C25391', 'ANALYSIS', '677236695'), ('C43360', 'MANUFACTURE', '677236695'), ('C84731', 'PACK', '677236695'), ('C84732', 'LABEL', '677236695')]; MANUFACTURE DUNS: ['677236695']; MANUFACTURE for other products: [('70069-651', '677236695'), ('70069-652', '677236695')].
- identity: 677236695 CURRENT_REGISTERED FEI 3003821988 (Somerset Therapeutics Private Limited)
- graph MANUFACTURE edges: 677236695 DIRECT []
- DailyMed today: latest v3 (1 versions); sampled version listed: True, published 2024-10-16
- free text (2 hits):
  - [MANUFACTURED_FOR] §42229-5  @0: “Manufactured for: Somerset Therapeutics, LLC Somerset, NJ 08873 Customer Care # 1-800-417-9175”
  - [MADE_IN] §42229-5  @95: “Made in India Code No.:KR/DRUGS/KTK/28/289/97 1201033 ST-BTT/P/00”
  - baseline: MANUFACTURED_FOR → company “Somerset Therapeutics” | location “LLC Somerset, NJ 08873 Customer Care # 1-800-417-9175” | label-establishment name match: True; DECRS exact-name rows: 1
  - baseline: MADE_IN → company “India Code No” | location “:KR/DRUGS/KTK/28/289/97 1201033 ST-BTT/P/00” | label-establishment name match: False; DECRS exact-name rows: 0
