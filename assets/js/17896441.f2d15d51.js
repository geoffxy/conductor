"use strict";(self.webpackChunkconductor=self.webpackChunkconductor||[]).push([[918],{3985:function(e,t,a){a.r(t),a.d(t,{default:function(){return te}});var n=a(7294),l=a(6010),i=a(3783),r=a(5999),s=a(9960);var o=function(e){var t=e.navLink,a=e.next;return n.createElement(s.Z,{className:(0,l.Z)("pagination-nav__link"),to:t.permalink},n.createElement("div",{className:"pagination-nav__sublabel"},a?n.createElement(r.Z,{id:"theme.docs.paginator.next",description:"The label used to navigate to the next doc"},"Next"):n.createElement(r.Z,{id:"theme.docs.paginator.previous",description:"The label used to navigate to the previous doc"},"Previous")),n.createElement("div",{className:"pagination-nav__label"},t.title))};var c=function(e){var t=e.previous,a=e.next;return n.createElement("nav",{className:"pagination-nav docusaurus-mt-lg","aria-label":(0,r.I)({id:"theme.docs.paginator.navAriaLabel",message:"Docs pages navigation",description:"The ARIA label for the docs pagination"})},n.createElement("div",{className:"pagination-nav__item"},t&&n.createElement(o,{navLink:t})),n.createElement("div",{className:"pagination-nav__item pagination-nav__item--next"},a&&n.createElement(o,{navLink:a,next:!0})))},d=a(2263),m=a(907),u=a(3616);var v={unreleased:function(e){var t=e.siteTitle,a=e.versionMetadata;return n.createElement(r.Z,{id:"theme.docs.versions.unreleasedVersionLabel",description:"The label used to tell the user that he's browsing an unreleased doc version",values:{siteTitle:t,versionLabel:n.createElement("b",null,a.label)}},"This is unreleased documentation for {siteTitle} {versionLabel} version.")},unmaintained:function(e){var t=e.siteTitle,a=e.versionMetadata;return n.createElement(r.Z,{id:"theme.docs.versions.unmaintainedVersionLabel",description:"The label used to tell the user that he's browsing an unmaintained doc version",values:{siteTitle:t,versionLabel:n.createElement("b",null,a.label)}},"This is documentation for {siteTitle} {versionLabel}, which is no longer actively maintained.")}};function g(e){var t=v[e.versionMetadata.banner];return n.createElement(t,e)}function h(e){var t=e.versionLabel,a=e.to,l=e.onClick;return n.createElement(r.Z,{id:"theme.docs.versions.latestVersionSuggestionLabel",description:"The label used to tell the user to check the latest version",values:{versionLabel:t,latestVersionLink:n.createElement("b",null,n.createElement(s.Z,{to:a,onClick:l},n.createElement(r.Z,{id:"theme.docs.versions.latestVersionLinkLabel",description:"The label used for the latest version suggestion link label"},"latest version")))}},"For up-to-date documentation, see the {latestVersionLink} ({versionLabel}).")}function p(e){var t,a=e.className,i=e.versionMetadata,r=(0,d.Z)().siteConfig.title,s=(0,m.gA)({failfast:!0}).pluginId,o=(0,u.J)(s).savePreferredVersionName,c=(0,m.Jo)(s),v=c.latestDocSuggestion,p=c.latestVersionSuggestion,E=null!=v?v:(t=p).docs.find((function(e){return e.id===t.mainDocId}));return n.createElement("div",{className:(0,l.Z)(a,u.kM.docs.docVersionBanner,"alert alert--warning margin-bottom--md"),role:"alert"},n.createElement("div",null,n.createElement(g,{siteTitle:r,versionMetadata:i})),n.createElement("div",{className:"margin-top--md"},n.createElement(h,{versionLabel:p.label,to:E.path,onClick:function(){return o(p.name)}})))}function E(e){var t=e.className,a=(0,u.E6)();return a.banner?n.createElement(p,{className:t,versionMetadata:a}):null}function b(e){var t=e.className,a=(0,u.E6)();return a.badge?n.createElement("span",{className:(0,l.Z)(t,u.kM.docs.docVersionBadge,"badge badge--secondary")},"Version: ",a.label):null}var f=a(1217);function N(e){var t=e.lastUpdatedAt,a=e.formattedLastUpdatedAt;return n.createElement(r.Z,{id:"theme.lastUpdated.atDate",description:"The words used to describe on which date a page has been last updated",values:{date:n.createElement("b",null,n.createElement("time",{dateTime:new Date(1e3*t).toISOString()},a))}}," on {date}")}function k(e){var t=e.lastUpdatedBy;return n.createElement(r.Z,{id:"theme.lastUpdated.byUser",description:"The words used to describe by who the page has been last updated",values:{user:n.createElement("b",null,t)}}," by {user}")}function L(e){var t=e.lastUpdatedAt,a=e.formattedLastUpdatedAt,l=e.lastUpdatedBy;return n.createElement("span",{className:u.kM.common.lastUpdated},n.createElement(r.Z,{id:"theme.lastUpdated.lastUpdatedAtBy",description:"The sentence used to display when a page has been last updated, and by who",values:{atDate:t&&a?n.createElement(N,{lastUpdatedAt:t,formattedLastUpdatedAt:a}):"",byUser:l?n.createElement(k,{lastUpdatedBy:l}):""}},"Last updated{atDate}{byUser}"),!1)}var _=a(7462),Z=a(3366),U="iconEdit_2_ui",C=["className"];var T=function(e){var t=e.className,a=(0,Z.Z)(e,C);return n.createElement("svg",(0,_.Z)({fill:"currentColor",height:"20",width:"20",viewBox:"0 0 40 40",className:(0,l.Z)(U,t),"aria-hidden":"true"},a),n.createElement("g",null,n.createElement("path",{d:"m34.5 11.7l-3 3.1-6.3-6.3 3.1-3q0.5-0.5 1.2-0.5t1.1 0.5l3.9 3.9q0.5 0.4 0.5 1.1t-0.5 1.2z m-29.5 17.1l18.4-18.5 6.3 6.3-18.4 18.4h-6.3v-6.2z"})))};function y(e){var t=e.editUrl;return n.createElement("a",{href:t,target:"_blank",rel:"noreferrer noopener",className:u.kM.common.editThisPage},n.createElement(T,null),n.createElement(r.Z,{id:"theme.common.editThisPage",description:"The link label to edit the current page"},"Edit this page"))}var w="tag_1Okp",A="tagRegular_3MiF",M="tagWithCount_1HU1";var H=function(e){var t,a=e.permalink,i=e.name,r=e.count;return n.createElement(s.Z,{href:a,className:(0,l.Z)(w,(t={},t[A]=!r,t[M]=r,t))},i,r&&n.createElement("span",null,r))},x="tags_2ga9",B="tag_11ep";function O(e){var t=e.tags;return n.createElement(n.Fragment,null,n.createElement("b",null,n.createElement(r.Z,{id:"theme.tags.tagsListLabel",description:"The label alongside a tag list"},"Tags:")),n.createElement("ul",{className:(0,l.Z)(x,"padding--none","margin-left--sm")},t.map((function(e){var t=e.label,a=e.permalink;return n.createElement("li",{key:a,className:B},n.createElement(H,{name:t,permalink:a}))}))))}var S="lastUpdated_13-_";function D(e){return n.createElement("div",{className:(0,l.Z)(u.kM.docs.docFooterTagsRow,"row margin-bottom--sm")},n.createElement("div",{className:"col"},n.createElement(O,e)))}function V(e){var t=e.editUrl,a=e.lastUpdatedAt,i=e.lastUpdatedBy,r=e.formattedLastUpdatedAt;return n.createElement("div",{className:(0,l.Z)(u.kM.docs.docFooterEditMetaRow,"row")},n.createElement("div",{className:"col"},t&&n.createElement(y,{editUrl:t})),n.createElement("div",{className:(0,l.Z)("col",S)},(a||i)&&n.createElement(L,{lastUpdatedAt:a,formattedLastUpdatedAt:r,lastUpdatedBy:i})))}function F(e){var t=e.content.metadata,a=t.editUrl,i=t.lastUpdatedAt,r=t.formattedLastUpdatedAt,s=t.lastUpdatedBy,o=t.tags,c=o.length>0,d=!!(a||i||s);return c||d?n.createElement("footer",{className:(0,l.Z)(u.kM.docs.docFooter,"docusaurus-mt-lg")},c&&n.createElement(D,{tags:o}),d&&n.createElement(V,{editUrl:a,lastUpdatedAt:i,lastUpdatedBy:s,formattedLastUpdatedAt:r})):null}var I=["toc","className","linkClassName","linkActiveClassName","minHeadingLevel","maxHeadingLevel"];function R(e){var t=e.toc,a=e.className,l=e.linkClassName,i=e.isChild;return t.length?n.createElement("ul",{className:i?void 0:a},t.map((function(e){return n.createElement("li",{key:e.id},n.createElement("a",{href:"#"+e.id,className:null!=l?l:void 0,dangerouslySetInnerHTML:{__html:e.value}}),n.createElement(R,{isChild:!0,toc:e.children,className:a,linkClassName:l}))}))):null}function z(e){var t=e.toc,a=e.className,l=void 0===a?"table-of-contents table-of-contents__left-border":a,i=e.linkClassName,r=void 0===i?"table-of-contents__link":i,s=e.linkActiveClassName,o=void 0===s?void 0:s,c=e.minHeadingLevel,d=e.maxHeadingLevel,m=(0,Z.Z)(e,I),v=(0,u.LU)(),g=null!=c?c:v.tableOfContents.minHeadingLevel,h=null!=d?d:v.tableOfContents.maxHeadingLevel,p=(0,u.DA)({toc:t,minHeadingLevel:g,maxHeadingLevel:h}),E=(0,n.useMemo)((function(){if(r&&o)return{linkClassName:r,linkActiveClassName:o,minHeadingLevel:g,maxHeadingLevel:h}}),[r,o,g,h]);return(0,u.Si)(E),n.createElement(R,(0,_.Z)({toc:p,className:l,linkClassName:r},m))}var P="tableOfContents_35-E",W=["className"];var q=function(e){var t=e.className,a=(0,Z.Z)(e,W);return n.createElement("div",{className:(0,l.Z)(P,"thin-scrollbar",t)},n.createElement(z,(0,_.Z)({},a,{linkClassName:"table-of-contents__link toc-highlight",linkActiveClassName:"table-of-contents__link--active"})))},J="tocCollapsible_1PrD",Y="tocCollapsibleButton_2O1e",j="tocCollapsibleContent_2Ydz",G="tocCollapsibleExpanded_3GYr";function K(e){var t,a=e.toc,i=e.className,s=e.minHeadingLevel,o=e.maxHeadingLevel,c=(0,u.uR)({initialState:!0}),d=c.collapsed,m=c.toggleCollapsed;return n.createElement("div",{className:(0,l.Z)(J,(t={},t[G]=!d,t),i)},n.createElement("button",{type:"button",className:(0,l.Z)("clean-btn",Y),onClick:m},n.createElement(r.Z,{id:"theme.TOCCollapsible.toggleButtonLabel",description:"The label used by the button on the collapsible TOC component"},"On this page")),n.createElement(u.zF,{lazy:!0,className:j,collapsed:d},n.createElement(z,{toc:a,minHeadingLevel:s,maxHeadingLevel:o})))}var Q=a(9649),X="docItemContainer_33ec",$="docItemCol_3FnS",ee="tocMobile_3Hoh";function te(e){var t,a=e.content,r=a.metadata,s=a.frontMatter,o=s.image,d=s.keywords,m=s.hide_title,v=s.hide_table_of_contents,g=s.toc_min_heading_level,h=s.toc_max_heading_level,p=r.description,N=r.title,k=!m&&void 0===a.contentTitle,L=(0,i.Z)(),_=!v&&a.toc&&a.toc.length>0,Z=_&&("desktop"===L||"ssr"===L);return n.createElement(n.Fragment,null,n.createElement(f.Z,{title:N,description:p,keywords:d,image:o}),n.createElement("div",{className:"row"},n.createElement("div",{className:(0,l.Z)("col",(t={},t[$]=!v,t))},n.createElement(E,null),n.createElement("div",{className:X},n.createElement("article",null,n.createElement(b,null),_&&n.createElement(K,{toc:a.toc,minHeadingLevel:g,maxHeadingLevel:h,className:(0,l.Z)(u.kM.docs.docTocMobile,ee)}),n.createElement("div",{className:(0,l.Z)(u.kM.docs.docMarkdown,"markdown")},k&&n.createElement(Q.N,null,N),n.createElement(a,null)),n.createElement(F,e)),n.createElement(c,{previous:r.previous,next:r.next}))),Z&&n.createElement("div",{className:"col col--3"},n.createElement(q,{toc:a.toc,minHeadingLevel:g,maxHeadingLevel:h,className:u.kM.docs.docTocDesktop}))))}},9649:function(e,t,a){a.d(t,{N:function(){return u},Z:function(){return v}});var n=a(3366),l=a(7462),i=a(7294),r=a(6010),s=a(5999),o=a(3616),c="anchorWithStickyNavbar_31ik",d="anchorWithHideOnScrollNavbar_3R7-",m=["id"],u=function(e){var t=Object.assign({},e);return i.createElement("header",null,i.createElement("h1",(0,l.Z)({},t,{id:void 0}),t.children))},v=function(e){return"h1"===e?u:(t=e,function(e){var a,u=e.id,v=(0,n.Z)(e,m),g=(0,o.LU)().navbar.hideOnScroll;return u?i.createElement(t,(0,l.Z)({},v,{className:(0,r.Z)("anchor",(a={},a[d]=g,a[c]=!g,a)),id:u}),v.children,i.createElement("a",{className:"hash-link",href:"#"+u,title:(0,s.I)({id:"theme.common.headingLinkTitle",message:"Direct link to heading",description:"Title for link to heading"})},"\u200b")):i.createElement(t,v)});var t}}}]);