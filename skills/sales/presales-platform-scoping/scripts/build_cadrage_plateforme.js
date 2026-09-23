/*
  Moteur de génération d'une NOTE DE CADRAGE TECHNIQUE DE LA PLATEFORME, charte.
  Usage : node build_cadrage_plateforme.js <analysis.json> <sortie.docx>
  - Tableaux dynamiques (décisions, composants, serveurs, services, budget, flux).
  - 2 points d'insertion de schéma (logique & physique) conservés (images ajoutées ensuite).
  - Tout champ absent ⇒ placeholder. Ne JAMAIS inventer de chiffres.
*/
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat,
  Footer, PageNumber, Tab, TabStopType, VerticalAlign
} = require('docx');
const fs = require('fs');

const INDIGO='3B3F7B', VIOLET='5742DE', ACCENT='4534B0', LAV_CLAIR='F3F2FB', LAV_MOYEN='BCBAEB', GRIS='6B6A85';
const W=9026;
const A = JSON.parse(fs.readFileSync(process.argv[2] || '/home/claude/analysis.json','utf8'));
const OUT = process.argv[3] || '/home/claude/PLAT_output.docx';
const has=(v)=> v!==undefined && v!==null && String(v).trim()!=='';
const val=(v,d)=> has(v)?String(v):(d!==undefined?d:null);

const run=(t,o={})=>new TextRun({text:t,font:'Calibri',...o});
const ph=(t)=>run(t,{italics:true,color:GRIS});
const lbl=(t)=>run(t,{bold:true,color:INDIGO});
const cellText=(v,dflt)=> has(v)?run(String(v)):ph(dflt||'[…]');
const p=(runs,o={})=>new Paragraph({children:Array.isArray(runs)?runs:[runs],...o});
const cb=(c=LAV_MOYEN,s=4)=>({top:{style:BorderStyle.SINGLE,size:s,color:c},bottom:{style:BorderStyle.SINGLE,size:s,color:c},left:{style:BorderStyle.SINGLE,size:s,color:c},right:{style:BorderStyle.SINGLE,size:s,color:c}});
function cell(width,fillC,children,o={}){return new TableCell({width:{size:width,type:WidthType.DXA},...(fillC?{shading:{type:ShadingType.CLEAR,fill:fillC,color:'auto'}}:{}),margins:{top:60,bottom:60,left:110,right:110},verticalAlign:VerticalAlign.CENTER,borders:cb(),children:Array.isArray(children)?children:[children],...o});}
const table=(cw,rows)=>new Table({columnWidths:cw,width:{size:W,type:WidthType.DXA},rows});
const sectionHeader=(t)=>new Paragraph({spacing:{before:300,after:120},border:{bottom:{style:BorderStyle.SINGLE,size:12,color:LAV_MOYEN,space:3}},children:[run(t,{bold:true,color:INDIGO,size:28})]});
const bullet=(t)=>new Paragraph({numbering:{reference:'puces',level:0},spacing:{after:60},children:[run(t)]});
const hc=(w,t)=>cell(w,LAV_MOYEN,p(run(t,{bold:true,color:INDIGO})));
const hrow=(cw,labels)=>new TableRow({tableHeader:true,children:labels.map((l,i)=>hc(cw[i],l))});
function schemaBox(t){return new Table({columnWidths:[W],width:{size:W,type:WidthType.DXA},rows:[new TableRow({children:[
  new TableCell({width:{size:W,type:WidthType.DXA},shading:{type:ShadingType.CLEAR,fill:LAV_CLAIR,color:'auto'},borders:cb(LAV_MOYEN,6),margins:{top:180,bottom:180,left:150,right:150},children:[p([run('▢  '+t,{italics:true,color:ACCENT})],{alignment:AlignmentType.CENTER})]})
]})]});}
// ligne de données : cells = [{v, plain?}]  (plain => texte noir ; sinon placeholder gris si vide)
function drow(cw, cells){return new TableRow({children:cells.map((c,i)=>cell(cw[i],null,p([ has(c.v) ? (c.plain?run(String(c.v)):run(String(c.v))) : ph(c.dflt||'[…]') ])))});}
// ligne total fusionnée
function totalRow(cw, labelSpanCount, label, valueText, trailingEmpty=0){
  const spanW = cw.slice(0,labelSpanCount).reduce((a,b)=>a+b,0);
  const children=[cell(spanW,LAV_CLAIR,p(run(label,{bold:true,color:INDIGO})),{columnSpan:labelSpanCount}),
                  cell(cw[labelSpanCount],LAV_CLAIR,p(run(valueText,{bold:true,color:INDIGO})))];
  for(let k=0;k<trailingEmpty;k++){children.push(cell(cw[labelSpanCount+1+k],LAV_CLAIR,p(run(''))));}
  return new TableRow({children});
}

const projet=val(A.projet), version=val(A.version,'0.1');
const CW2=[2000,2200,2600,2226], CW4=[2000,2200,1400,1800,1626], CW6=[2600,1400,2400,900,1726], CW7=[2200,1900,2100,1500,1326], CW8=[3800,2600,2626], CW10=[700,2400,2400,2200,1326];

const decisions=Array.isArray(A.decisions)&&A.decisions.length?A.decisions:[{}];
const composants=Array.isArray(A.composants)&&A.composants.length?A.composants:[{}];
const serveurs=Array.isArray(A.serveurs)&&A.serveurs.length?A.serveurs:[{}];
const services=Array.isArray(A.services)&&A.services.length?A.services:[{}];
const flux=Array.isArray(A.flux)&&A.flux.length?A.flux:[{}];
const bud=A.budget||{};

const doc=new Document({
  styles:{default:{document:{run:{font:'Calibri',size:22,color:'1A1A1A'}}}},
  numbering:{config:[{reference:'puces',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:360,hanging:260}}}}]}]},
  sections:[{
    properties:{page:{margin:{top:1440,right:1440,bottom:1440,left:1440}}},
    footers:{default:new Footer({children:[new Paragraph({tabStops:[{type:TabStopType.RIGHT,position:W}],children:[
      run('Confidentiel — document de travail',{color:GRIS,size:16}),
      new TextRun({children:[new Tab()]}),
      run('Page ',{color:GRIS,size:16}),
      new TextRun({children:[PageNumber.CURRENT],color:GRIS,size:16,font:'Calibri'}),
      run(' / ',{color:GRIS,size:16}),
      new TextRun({children:[PageNumber.TOTAL_PAGES],color:GRIS,size:16,font:'Calibri'}),
    ]})]})},
    children:[
      p(run('Note de cadrage technique de la plateforme',{bold:true,color:INDIGO,size:38}),{spacing:{after:60}}),
      p([has(projet)?run(projet,{italics:true,color:GRIS,size:24}):run('[Projet]',{italics:true,color:GRIS,size:24}),run(' — Architecture technique et estimation budgétaire',{italics:true,color:GRIS,size:24})],{spacing:{after:120}}),
      p([lbl('Arnaud BRETON'),run('  ·  ',{color:GRIS}),run('v'+version+' · Proposition · document de travail',{bold:true,color:VIOLET})],{spacing:{after:120}}),
      p([run("Cette note cadre la plateforme technique (composants, flux, serveurs, services tiers, coûts). Elle est distincte du cadrage fonctionnel de l'application SaaS, qui décrit les besoins métier et les parcours utilisateurs. Les schémas sont indicatifs et servent de base de co-construction ; ils évolueront par itérations.",{italics:true,color:GRIS})]),

      sectionHeader('1.  Objet et périmètre'),
      p([run("Objectif de la note : partager une vision technique cible de la plateforme, cadrer la partie serveurs, et fournir une première estimation budgétaire (coûts récurrents et coûts de mise en place).")],{spacing:{after:80}}),
      bullet('Inclus : architecture technique, flux, composants serveurs, services tiers, exploitation, budget indicatif.'),
      bullet('Exclu : cadrage fonctionnel de l’application (parcours, règles métier, backlog), traité séparément.'),

      sectionHeader('2.  Décisions et hypothèses structurantes'),
      table(CW2,[hrow(CW2,['Décision','Choix retenu','Justification','Condition de remise en cause']),
        ...decisions.map(d=>drow(CW2,[{v:d.decision},{v:d.choix},{v:d.justification,dflt:'[à justifier]'},{v:d.condition,dflt:'[signal de remise en cause]'}]))]),

      sectionHeader('3.  Vue fonctionnelle de la plateforme'),
      schemaBox('Insérer le schéma des flux fonctionnels — image exportée depuis l’éditeur de schémas (schéma logique)'),
      p([run("Commentaire : présentation des grandes briques fonctionnelles et de la circulation de l'information, indépendamment de toute technologie.")],{spacing:{before:100}}),

      sectionHeader('4.  Référentiel des composants techniques'),
      table(CW4,[hrow(CW4,['Composant','Technologie / Produit','Version','Hébergement','Serveur']),
        ...composants.map(c=>drow(CW4,[{v:c.composant},{v:c.techno},{v:c.version,dflt:'—'},{v:c.hebergement},{v:c.serveur}]))]),

      sectionHeader('5.  Architecture technique'),
      schemaBox('Insérer le schéma d’architecture technique — image exportée depuis l’éditeur de schémas (schéma physique)'),
      p([run("Commentaire : rôles techniques et déploiement logique. L'API Métier est un point d'entrée unique qui encapsule les API tierces (surcouche). Le CDN diffuse les assets JS/CSS et les médias.")],{spacing:{before:100}}),

      sectionHeader('6.  Composants serveurs et dimensionnement'),
      table(CW6,[hrow(CW6,['Composant','Type','Dimensionnement','Qté','Coût /mois (est.)']),
        ...serveurs.map(s=>drow(CW6,[{v:s.composant},{v:s.type},{v:s.dim},{v:s.qte},{v:s.cout,dflt:'[€ …]'}])),
        totalRow(CW6,4,'Total récurrent',val(A.serveurs_total,'[€ … / mois]')),
        totalRow(CW6,4,'Mise en place (DevOps, déploiement) — coût unique',val(A.serveurs_miseenplace,'[€ … one-shot]')),
      ]),

      sectionHeader('7.  Services tiers (API externes)'),
      table(CW7,[hrow(CW7,['Catégorie','Intégration','Modèle tarifaire','Coût /mois (est.)','Criticité']),
        ...services.map(s=>drow(CW7,[{v:s.categorie},{v:s.integration},{v:s.tarif},{v:s.cout,dflt:'[€ …]'},{v:s.criticite}])),
        totalRow(CW7,3,'Total récurrent',val(A.services_total,'[€ … / mois]'),1),
        totalRow(CW7,3,"Intégration de l'ensemble des services — temps de mise en place",val(A.services_integration,'[… j/h]'),1),
      ]),

      sectionHeader('8.  Estimation budgétaire (synthèse)'),
      table(CW8,[hrow(CW8,['Poste','Nature','Montant (est.)']),
        drow(CW8,[{v:'Composants serveurs'},{v:'Récurrent mensuel'},{v:bud.serveurs_mois,dflt:'[€ … / mois]'}]),
        drow(CW8,[{v:'Services tiers'},{v:'Récurrent mensuel'},{v:bud.services_mois,dflt:'[€ … / mois]'}]),
        new TableRow({children:[cell(CW8[0],LAV_CLAIR,p(run('Total récurrent',{bold:true,color:INDIGO}))),cell(CW8[1],LAV_CLAIR,p(run('Fonctionnement',{bold:true,color:INDIGO}))),cell(CW8[2],LAV_CLAIR,p(run(val(bud.total_mois,'[€ … / mois]'),{bold:true,color:INDIGO})))]}),
        drow(CW8,[{v:'Mise en place infrastructure (DevOps, déploiement)'},{v:'Coût unique'},{v:bud.miseenplace,dflt:'[€ …]'}]),
        drow(CW8,[{v:'Intégration des services tiers'},{v:'Charge projet'},{v:bud.integration,dflt:'[… j/h]'}]),
      ]),
      p([run('Montants indicatifs, à consolider avec les devis de l’hébergeur et des fournisseurs tiers.',{italics:true,color:GRIS})],{spacing:{before:80}}),

      sectionHeader('9.  Exploitation (run)'),
      bullet('Supervision et métriques.'),
      bullet('Journalisation centralisée et traces.'),
      bullet('Alerting et astreinte.'),
      bullet('Sauvegardes et restauration.'),

      sectionHeader('10.  Matrice de flux'),
      p([run('Destinée aux équipes sécurité et réseau. Adresses IP à confirmer (plan d’adressage indicatif).')],{spacing:{after:80}}),
      table(CW10,[hrow(CW10,['ID','Source','Destination','Protocole · Port','Sens d’init.']),
        ...flux.map(f=>drow(CW10,[{v:f.id},{v:f.source},{v:f.destination},{v:f.protoport},{v:f.sens}]))]),

      sectionHeader('11.  Prochaines étapes'),
      bullet('Valider les décisions structurantes et les hypothèses de dimensionnement.'),
      bullet('Consolider les coûts avec les devis hébergeur et fournisseurs.'),
      bullet('Itérer sur l’architecture selon les retours.'),
    ],
  }],
});

Packer.toBuffer(doc).then((buf)=>{fs.writeFileSync(OUT,buf);console.log('OK',OUT,buf.length,'bytes');});
