import csv,json,pathlib
R=pathlib.Path(__file__).parent; M=R/'market'
def write(name,rows):
 with (M/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
food='https://vancouverfoodster.com/openings/'
# published opening signals; not statements about deficiencies or purchase intent
raw='''Doe Coffee|Olympic Village|announced November|doecoffeeroasters
Hello Nori|Oakridge Park|announced November|hellonori
Trees Cheesecake + Organic Coffee|Oakridge Park|announced November|treescoffee
Cha House Bubble Tea|Oakridge Park|announced November|
Moonies Bagels|227 E Pender|announced December|mooooonies_
Sammi & Soupe Dumpling|2129 West 41st|announced December|sammi_soupe_dumpling
Obsidian Bakehouse|1758 W Broadway|announced December|obsidian.bakehouse
Herschel’s Deli and Shmeer|1500 West 2nd|announced December|
Aiyaohno Parlour|214 Abbott|announced fall|aiyaohno.parlour
Bento Cafe|2156 W 41st|announced December|bentocafeyvr
Tucci’s|4410 Fraser|announced fall|
Oora Coffee|6045 West Boulevard|announced date pending|
Earnest Ice Cream|1431 Anderson|announced fall|earnesticecream
Angus T Bakery & Cafe|660 W Cordova|announced date pending|angustbakery
Nami Vietnamese|3030 Main|announced fall|
¿CóMO? Ultramar|592 E Broadway|announced winter|
Mandhras Cafe|382 W Broadway|announced fall|
Kebab on Fire|1637 Manitoba|announced date pending|
Field and Social|South Flats|announced fall|fieldandsocial
Celeste Cafe|510 W Hastings|announced fall|celeste510hastings
Lee’s Donuts|141 West 49th|announced fall|leesdonuts.ca
Archr Coffee|2961 Cambridge, Port Coquitlam|announced winter|archrcoffee
Pizza Rubato Napoletana|1090 W Pender|announced January 2027|pizzarubato
Avik|Coal Harbour|announced date pending|avikcafe
Disco Cheetah|Lonsdale Quay, North Vancouver|announced date pending|discocheetahyvr
Brazil Gourmet|Lonsdale Quay, North Vancouver|announced date pending|
Catcher in the Fry|Lonsdale Quay, North Vancouver|announced date pending|
Crave Cheesesteaks|Lonsdale Quay, North Vancouver|announced date pending|cravecheesesteaks
Tiny Twins Cafe|Granville & 14th|announced date pending|tinytwins.inc
Creatures Coffee|1345 Clark|listed now open|creaturescoffeeyvr
Rosalia Osteria|1127 Mainland|listed now open|rosaliayvr
Emilee’s Sweet House|100 E 2nd, North Vancouver|listed now open|emilees_sweet_house
Gimme Brazilian Bakery|2766 W 4th|listed now open|gimmebakery
Greyhound Tavern|1908 Rosser, Burnaby|listed now open|greyhoundtavern.fc
Zumi Revolving Sushi Bar|1588 Alberni|listed now open|zumisushi_ca
C Market Coffee|1185 W Georgia|listed now open|cmarket_coffee
Coasters Coffee|4510 Rupert|listed now open|coasterscoffeeshop
Haisan|2892 Commercial|listed now open|haisan.ca
One More Scoop|1939 Cornwall|listed now open|getonemorescoop
Burdy Sandwiches|1441 Anderson|listed now open|burdy_sandwiches
Four Bite Burger|Bentall Centre|listed now open|fourbiteburger
Some Cafe & Bar|281 17th, West Vancouver|listed now open|somecafebar
Kuun Thai Cuisine|7413 Edmonds, Burnaby|listed now open|kuunthaicuisine
Elaichi Patisserie|2821 Main|listed now open|elaichipatisserie
Helios Patisserie|2896 Commercial|listed now open|helios.cdr'''
leads=[]
for i,line in enumerate(raw.splitlines(),1):
 name,loc,signal,handle=line.split('|');offer='C04 launch visibility' if signal.startswith('announced') else 'C02 local discovery and inquiry review';
 leads.append(dict(id=f'SIG-{i:03}',company=name,industry='Food / hospitality',location=loc+', Metro Vancouver, BC',signal=signal,source_url=food,checked='2026-11-25',evidence=f'Publisher lists {name} at {loc} as {signal}. Confirm current status directly.',need_hypothesis='Confirm local discovery, accurate hours/menu and inquiry or ordering flow; no deficiency established.',offer=offer,contact_route=('https://www.instagram.com/'+handle+'/' if handle else 'Find official business contact or permitted in-person introduction'),consent_basis='NOT VERIFIED; public channel is not consent',status='RESEARCH',owner='Sales operator (unassigned)',next_action='Verify current status, decision-maker, existing digital journey and permissible channel',priority='B' if 'date pending' not in signal else 'C'))
for name,loc,signal,url in [('Renfrew Family Dental','East Vancouver','clinic announces early 2027 opening','https://www.renfrewfamilydental.ca/about'),('Medlux Medical Clinic','3265 Heather','new licence Nov 20','https://ribbonmap.com/vancouver?cat=Health+%26+Medical&group=all'),('Movement Room Health Main Inc.','2337 Main','new licence Nov 18','https://ribbonmap.com/vancouver?cat=Health+%26+Medical&group=all'),('Medora Health Centre','1065 Seymour','new licence Nov 17','https://ribbonmap.com/vancouver?cat=Health+%26+Medical&group=all'),('Guest List','Downtown Vancouver','new salon licence Nov 5','https://ribbonmap.com/vancouver/b/guest-list-704c7f2')]:
 leads.append(dict(id=f'SIG-{len(leads)+1:03}',company=name,industry='Beauty' if name=='Guest List' else 'Health services',location=loc+', Metro Vancouver, BC',signal=signal,source_url=url,checked='2026-11-25',evidence=f'{name}: {signal} per linked source; licence is not proof of opening.',need_hypothesis='Verify public discovery and non-sensitive booking flow; do not request health data.',offer='C05 booking inquiry assessment / C04 launch',contact_route='Find official business contact or permitted introduction',consent_basis='NOT VERIFIED',status='RESEARCH',owner='Sales operator (unassigned)',next_action='Confirm business status, official contact, decision-maker and permitted outreach; avoid patient data',priority='B'))
assert len(leads)==50;write('buying_signals.csv',leads)
# Competitor screening; explicitly mark missing rather than infer reviews or financial outcomes
cl='https://clutch.co/ca/agencies/digital/vancouver'; dm='https://clutch.co/ca/agencies/digital-marketing/vancouver'
comp='''BHP Solution|https://bhpsolution.com/persian-campaign|Persian/Canadian business|web, marketing, startup, automation|Not verified|Free consultation; Persian campaign|Pailux Home Design testimonial on own site; Feedeo project on site|Bilingual integrated scope
Metro Pars|https://www.metropars.com/en/packages/|Persian business owners|bilingual websites, SEO, CRM, booking|CAD 1190–5490 website; booking 389; CRM 519; care 29/mo|Free bilingual consultation|Independent reviews not checked|Fixed prices and Persian support
Meta Marketing|https://metamarketing.ca/|Multicultural communities|digital and print marketing|Not verified|Community media|Not checked|Persian and other community reach
VancouverAgency.ca|https://vancouveragency.ca/pricing/|Local businesses|marketing, funnel review, SEO|See public pricing page; figures not extracted|Free audit and conversation|Not checked|Transparent starting scope
VanDesign|https://vandesign.ca/services/digital-strategy-consulting-vancouver|Local businesses|digital strategy and audits|Fixed project prices; range not extracted|Consulting page|Not checked|Comprehensive audit
North SEO|https://northseo.ca/store|SEO buyers|SEO audit, digital strategy|CAD 997 strategy|Online store|Not checked|Direct purchase option
Vancouver.Agency|https://www.vancouver.agency/pricing|BC businesses|digital acquisition, SEO, conversion|1997–3997 conversion audit (currency not confirmed)|Public pricing|Not checked|Clearly scoped audit
withY|https://withy.ca/prices/|Vancouver businesses|marketing and audits|500–2000 PPC audit; currency not confirmed|Price page|Not checked|Transparent pricing
Setsail Marketing|https://www.setsail.ca/pricing|Businesses|social media, website planning|See pricing page|Public pricing|Clutch summary available; not individually read|Audience research and analytics
Vancouver SEO Agency|https://vancouverseoagency.ca/seo/competitor-seo-analysis/|SEO clients|competitor SEO analysis|Not extracted|Service page|Not checked|Specialized competitor offering
Olive Grey Creative|https://www.olivegreycreative.com/pricing|Website clients|design and audit|Varies by scope|Pricing page|Not checked|Conversion audit
RMBT|https://rankmybusiness.today/pricing/|Local businesses|websites and digital marketing|CAD 4490+ website|Price page|Not checked|Scope includes inquiry and analytics
Two Trees Studio|https://twotreesstudio.ca/services/web-consulting/|Canadian businesses|web consulting and audits|390+ written audit; currency not explicitly checked|Free SEO audit|Not checked|Client owns report
Vancouver.Marketing|https://vancouver.marketing/pricing/|Local businesses|SEO and web design|500–2000 SEO audit; currency not confirmed|Price page|Not checked|Competitor monitoring
Takt|CL|Larger brand projects|design and digital marketing|25000+ minimum; 200–300/hr|Clutch profile|Directory reports positive communication|Creative quality
Unite Interactive|CL|Digital projects|design and marketing|10000+ minimum; 100–149/hr|Clutch profile|17/20 directory review score|Cross-discipline
Blue Meta|CL|Digital projects|digital marketing and design|1000+ minimum; 150–199/hr|Clutch profile|15.8/20 directory review score|Marketing emphasis
Major Tom|CL|Larger clients|marketing and digital design|50000+ minimum; 150–199/hr|Clutch profile|19.4/20 directory review score|Broad execution
Ballistic Arts|CL|Digital projects|digital marketing and design|5000+ minimum; 150–199/hr|Clutch profile|16.2/20 directory review score|Regional presence
Rare Design Group|CL|Design projects|digital design, marketing|1000+ minimum; 100–149/hr|Clutch profile|16.2/20 directory review score|Design focus
Talk Shop|CL|Digital projects|design, marketing|10000+ minimum|Clutch profile|18.6/20 directory review score|Marketing and communications
Matrix Bricks|CL|Digital projects|digital marketing and design|1000+ minimum; 25–49/hr|Clutch profile|16.8/20 directory review score|Accessible project minimum
Forge & Spark Media|CL|Digital projects|digital marketing and design|5000+ minimum; 150–199/hr|Clutch profile|16.2/20 directory review score|Marketing specialization
Forge and Smith|CL|Digital projects|digital design, marketing|10000+ minimum; 150–199/hr|Clutch profile|16.2/20 directory review score|Design emphasis
The REX Agency|CL|Digital projects|digital design, marketing|5000+ minimum; 150–199/hr|Clutch profile|17.4/20 directory review score|Regional design
Longevity Graphics|CL|Digital projects|design and marketing|1000+ minimum; 100–149/hr|Clutch profile|17.2/20 directory review score|Balanced delivery
Pace Creative Group|CL|Digital projects|design and marketing|10000+ minimum; 150–199/hr|Clutch profile|16/20 directory review score|Creative scope
1UP Digital Marketing|https://clutch.co/profile/1up-digital-marketing|Digital marketing clients|SEO, paid ads, CRO|Not extracted|Clutch profile|Long-term client reports nine years of service|Retention model evidenced
 dNOVO|https://clutch.co/profile/dnovo-digital-marketing-seo-agency|Digital marketing clients|SEO, PPC, web, content|Not extracted|Clutch profile|Positive review summary; individual critique not audited|In-house specialist team
Longhouse Branding & Marketing|DM|Regional businesses|branding, web, SEO, ads|Not extracted|Clutch profile|Directory reports positive feedback|Integrated services'''
cs=[]
for line in comp.splitlines():
 n,u,t,s,p,f,review,adv=line.split('|');cs.append(dict(competitor=n.strip(),source_url={'CL':cl,'DM':dm}.get(u,u),target=t,services=s,published_price=p,acquisition_observed=f,review_evidence=review,advantage=adv,weakness='No independently documented negative finding; audit required',portfolio='Only if specifically referenced in review/evidence; otherwise not checked',recurring_model='Not verified' if n not in ['Metro Pars','1UP Digital Marketing'] else ('Published care plan' if n=='Metro Pars' else 'Long-term paid marketing relationship reported; pricing unknown'),ad_library='Not checked',conversion_funnel=f,profitable_service='Unknown; revenue/margin not public',checked='2026-11-25',depth='initial screening, not full audit'))
assert len(cs)==30;write('competitors.csv',cs)
channels=[('Persian Business Network','https://pbnetwork.ca/','Metro Vancouver','Business networking; nonprofit','Ask about event introductions and member promotion'),('PVfans','https://pvfans.ca/','Vancouver','Community media; advertising page','Request media kit and recent actual views'),('Malooos','https://malooos.com/browse/city/vancouver','Vancouver','Directory of Persian groups','Check each group rules and actual activity'),('Pelk','https://www.pelk.ca/','Canada','Persian business directory','Check listing eligibility and cost'),('CAIRAN','https://www.cairan.ca/en','Canada','Business directory and partnerships','Request ad rules and geographic reach'),('IranianInfo','https://www.iranianinfo.ca/about-us/members','Vancouver','Association; member promotions','Check membership and publication terms'),('Vancouver SeaBuzz','https://vancouverseabuzz.com/','Metro Vancouver','Persian/English print and online','Request current distribution evidence and rates'),('Vancobiz Club','https://club.vancobiz.com/contact/','Vancouver','Persian business networking','Ask about participation and introductions'),('Niyazmandiha Online','https://niyazmandihaonline.com/about/','Canada','Free directory per site','Check listing submission and actual reach'),('PersiansHome','https://persianshome.com/in/ca/vancouver','Vancouver','Community directory','Check posting rules and visibility')]
write('channels.csv',[dict(name=n,url=u,geography=g,observed_type=t,next_action=a,rate='Not verified',activity='Not measured',ad_rules='Not independently checked',prior_ad_performance='Not available',status='RESEARCH') for n,u,g,t,a in channels])
print(len(cs),len(leads),len(channels))
