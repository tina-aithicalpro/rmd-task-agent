-- RMD Task Agent - Seed Data
-- 6 services + 56 tasks (32 ClickUp origin, 24 project origin P-01..P-24).
-- Statuses reflect decisions locked in the pipeline design session.

-- ---------------------------------------------------------------------------
-- SERVICES (locked six pillars)
-- ---------------------------------------------------------------------------
INSERT INTO services (name, brand, note) VALUES
('Medical aesthetics', 'RMD', 'Injectables: Dysport and Xeomin ONLY. Botox is a hard stop until Dr. Vaidya confirms.'),
('Hormone therapy', 'RMD', NULL),
('Functional medicine', 'RMD', NULL),
('Medical weight loss', 'RMD', 'Semaglutide.'),
('Peptide therapy', 'PTR', 'Delivered under PTR brand.'),
('Stem cell therapy', 'PTR', 'Delivered under PTR brand. Investigational framing required.');

-- ---------------------------------------------------------------------------
-- CLICKUP-ORIGIN TASKS (32). external_ref = 'clickup-N'.
-- Statuses: #1,#2,#29 in progress; #5,#27 on hold client; rest to_do.
-- #29 in progress AND internal_blocked (Ashish account IDs).
-- ---------------------------------------------------------------------------
INSERT INTO tasks (origin, external_ref, title, status, task_type, cadence, assignee, internal_blocked, blocker_note, workstream) VALUES
('clickup','clickup-1','Respond to all Yelp and Google reviews','in_progress','recurring','weekly',NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-2','Myca reel for RegenesisMD','in_progress','one_shot',NULL,'Gul',FALSE,'Awaiting Gul creative direction','AI Visibility'),
('clickup','clickup-3','ABBO content, Regenesis QA, ILU indexing, AMC domain transfer','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-4','Privacy policy triple-check + add cookie policy','to_do','one_shot',NULL,'Cherry',FALSE,NULL,'Website'),
('clickup','clickup-5','Finalize tutorial videos, then proceed to reels','on_hold_client','one_shot',NULL,'Gul',FALSE,'Jay script approval','AI Visibility'),
('clickup','clickup-6','Write and distribute AP wire press release','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-7','Claim WebMD listing','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-8','Claim Healthgrades listing','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-9','Claim RealSelf listing','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-10','Claim Zocdoc listing','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-11','Claim Vitals.com listing','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-12','Claim AmericanMedSpa.org listing','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-13','Pitch Voyage Raleigh editorial feature','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-14','Reddit r/raleigh community citation post','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-15','Build Google Reviews volume - request flow','to_do','recurring','weekly',NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-16','Add physician-oversight FAQ to homepage','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-17','Add best medical spa Raleigh FAQ to homepage','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-18','Add weight-loss FAQ to semaglutide page','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-19','Fix geo-specificity on all FAQs (Raleigh NC)','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-20','Add comparison FAQ to homepage','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-21','Remove prohibited word delve on /disease-prevention','to_do','one_shot',NULL,NULL,FALSE,'LIVE compliance defect - prohibited word on live page','AI Visibility'),
('clickup','clickup-22','Confirm GSC sitemap submitted (78 URLs)','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-23','Run Google Indexing API batch (78 URLs)','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-24','Verify 301 redirects from Showit slugs','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-25','Sitewide compliance audit via Claude in Chrome','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-26','Confirm /membership FAQPage schema deployed','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-27','Confirm peptide blend names (Glow/Klow), then publish','on_hold_client','one_shot',NULL,NULL,FALSE,'Dr. Vaidya confirmation','AI Visibility'),
('clickup','clickup-28','Build Membership page FAQ block (4 Q+As)','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-29','Configure Blotato publishing pipeline','in_progress','one_shot',NULL,NULL,TRUE,'Needs account IDs from Ashish','AI Visibility'),
('clickup','clickup-30','Add AP wire press URL to sameAs schema','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-31','Publish 2 blog posts per month','to_do','recurring','monthly',NULL,FALSE,NULL,'AI Visibility'),
('clickup','clickup-32','Secure one more local editorial placement','to_do','one_shot',NULL,NULL,FALSE,NULL,'AI Visibility');

-- ---------------------------------------------------------------------------
-- PROJECT-ORIGIN TASKS (24). external_ref = 'P-NN'.
-- ---------------------------------------------------------------------------
INSERT INTO tasks (origin, external_ref, title, status, task_type, cadence, assignee, internal_blocked, blocker_note, duplicate_of, workstream) VALUES
('project','P-01','Build competitor profile sheet, 5 RMD competitors','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Competitor Intel'),
('project','P-02','Confirm Blue Water Spa + Synergy as primary competitors in tracking','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Competitor Intel'),
('project','P-03','Pull competitor active ads (Meta + Google Transparency)','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Competitor Intel'),
('project','P-04','Document competitors entering peptides/stem cells','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Competitor Intel'),
('project','P-05','Map competitor Meta follower audiences for acquisition','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Competitor Intel'),
('project','P-06','Audit Shopify storefront purchase flow end to end','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Shopify'),
('project','P-07','Map all SKUs for post-purchase refill reminders','on_hold_internal','one_shot',NULL,'Tina',FALSE,'Ashish (HIPAA/Ken handoff)',NULL,'Shopify'),
('project','P-08','Spec loyalty/points layer, reconcile with Lotus Membership','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Shopify'),
('project','P-09','Draft why-buy-from-us product-page value content','on_hold_internal','one_shot',NULL,'Tina',FALSE,'Product photos (Jean/Cameron)',NULL,'Shopify'),
('project','P-10','Surface Shopify AI-layer opportunities','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Shopify'),
('project','P-11','Simplify appointment-booking path','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Website'),
('project','P-12','Add deposit-capture at online booking','on_hold_internal','one_shot',NULL,'Tina',FALSE,'Ashish + Cameron sign-off',NULL,'Website'),
('project','P-13','Spec dynamic personalization (returning-visitor routing)','to_do','one_shot',NULL,'Tina',FALSE,NULL,NULL,'Website'),
('project','P-14','Send itemized cost recap email to Ashish','to_do','one_shot',NULL,'Jay',FALSE,'Flagged single most urgent deliverable',NULL,'Commercial'),
('project','P-15','Connect with Ken Baratsa, confirm HIPAA status','to_do','one_shot',NULL,'Jay',FALSE,NULL,NULL,'Commercial'),
('project','P-16','Launch RMD email campaigns','on_hold_internal','one_shot',NULL,NULL,FALSE,'Blocked on Ken HIPAA confirmation',NULL,'Commercial'),
('project','P-17','Create T Room teaser content','on_hold_internal','one_shot',NULL,NULL,FALSE,'Awaiting T Room videos from Ashish',NULL,'T Room'),
('project','P-18','Build T Room website','to_do','one_shot',NULL,NULL,FALSE,'$3,500 one-time. Active engagement',NULL,'T Room'),
('project','P-19','Optimize AMC Legacy Builders website','to_do','one_shot',NULL,NULL,FALSE,'$1,000 one-time. Informational scope only',NULL,'AMC'),
('project','P-20','Coordinate three-way call (Bob Nascale, inventory system)','on_hold_internal','one_shot',NULL,'Jay',FALSE,'Deferred until workload stabilizes',NULL,'Commercial'),
('project','P-21','Absorb site maintenance into retainer (2-month deadline)','to_do','one_shot',NULL,'Jay',FALSE,'Deadline 2 months from June 2026',NULL,'Commercial'),
('project','P-22','AMC Legacy Builders domain transfer','to_do','one_shot',NULL,NULL,FALSE,'Overlaps ClickUp #3',NULL,'AMC'),
('project','P-23','Define referral program tiers in recap email','to_do','one_shot',NULL,'Jay',FALSE,'Policy resolved 7-15%; tiers still to define',NULL,'Commercial'),
('project','P-24','Social media production cadence','to_do','recurring','twice_weekly',NULL,FALSE,'3 videos/week + daily content',NULL,'AI Visibility');

-- P-22 duplicate_of set separately to reference the real clickup-3 row id at load time
-- (external_ref clickup-3). Handled in validation script rather than hardcoding a serial id.
