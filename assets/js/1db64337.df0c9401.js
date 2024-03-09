"use strict";(self.webpackChunkconductor=self.webpackChunkconductor||[]).push([[413],{4339:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>d,contentTitle:()=>i,default:()=>u,frontMatter:()=>o,metadata:()=>a,toc:()=>c});var s=n(4848),r=n(8453);const o={title:"Overview",slug:"/"},i=void 0,a={id:"overview",title:"Overview",description:"Conductor is a simple and elegant tool that helps orchestrate your research",source:"@site/docs/overview.md",sourceDirName:".",slug:"/",permalink:"/conductor/",draft:!1,unlisted:!1,editUrl:"https://github.com/geoffxy/conductor/edit/master/website/docs/overview.md",tags:[],version:"current",frontMatter:{title:"Overview",slug:"/"},sidebar:"docs",next:{title:"Task Types",permalink:"/conductor/task-types"}},d={},c=[{value:"Installing",id:"installing",level:2},{value:"Getting Started",id:"getting-started",level:2},{value:"Project Root",id:"project-root",level:3},{value:"Tasks",id:"tasks",level:3},{value:"Task Identifiers",id:"task-identifiers",level:4},{value:"Dependencies",id:"dependencies",level:4},{value:"Task Outputs",id:"task-outputs",level:4}];function l(e){const t={a:"a",code:"code",em:"em",h2:"h2",h3:"h3",h4:"h4",p:"p",pre:"pre",...(0,r.R)(),...e.components};return(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(t.p,{children:"Conductor is a simple and elegant tool that helps orchestrate your research\ncomputing. Conductor automates your research computing pipeline, all the way\nfrom experiments to figures in your paper."}),"\n",(0,s.jsx)(t.h2,{id:"installing",children:"Installing"}),"\n",(0,s.jsx)(t.p,{children:"Conductor requires Python 3.8+ and is currently only supported on macOS and\nLinux machines. It has been tested on macOS 10.14 and Ubuntu 20.04."}),"\n",(0,s.jsxs)(t.p,{children:["Conductor is ",(0,s.jsx)(t.a,{href:"https://pypi.org/project/conductor-cli/",children:"available on PyPI"})," and so\nit can be installed using ",(0,s.jsx)(t.code,{children:"pip"}),"."]}),"\n",(0,s.jsx)(t.pre,{children:(0,s.jsx)(t.code,{className:"language-bash",children:"pip install conductor-cli\n"})}),"\n",(0,s.jsxs)(t.p,{children:["After installation, the ",(0,s.jsx)(t.code,{children:"cond"})," executable should be available in your shell."]}),"\n",(0,s.jsx)(t.pre,{children:(0,s.jsx)(t.code,{className:"language-bash",children:"cond --help\n"})}),"\n",(0,s.jsx)(t.h2,{id:"getting-started",children:"Getting Started"}),"\n",(0,s.jsxs)(t.p,{children:["A quick way to get started is to look at Conductor's ",(0,s.jsx)(t.a,{href:"https://github.com/geoffxy/conductor/tree/master/examples",children:"example\nprojects"}),". Below is a\nquick overview of a few important Conductor concepts."]}),"\n",(0,s.jsx)(t.h3,{id:"project-root",children:"Project Root"}),"\n",(0,s.jsxs)(t.p,{children:["When using Conductor with your project, you first need to add a\n",(0,s.jsx)(t.code,{children:"cond_config.toml"})," file to your project's root directory. This file tells\nConductor where your project files are located and is important because all\ntask identifiers (defined below) are relative to your project root."]}),"\n",(0,s.jsx)(t.h3,{id:"tasks",children:"Tasks"}),"\n",(0,s.jsxs)(t.p,{children:['Conductor works with "tasks", which are jobs (arbitrary shell commands or\nscripts) that it should run. You define tasks in ',(0,s.jsx)(t.code,{children:"COND"}),' files using Python\nsyntax. All tasks are of a predefined "type" (e.g., ',(0,s.jsx)(t.code,{children:"run_experiment()"}),"), which\nare listed in the ",(0,s.jsx)(t.a,{href:"task-types",children:"task types reference documentation"}),"."]}),"\n",(0,s.jsxs)(t.p,{children:["Conductor's tasks are very similar to (and inspired by)\n",(0,s.jsx)(t.a,{href:"https://bazel.build",children:"Bazel's"})," and ",(0,s.jsx)(t.a,{href:"https://buck.build",children:"Buck's"})," build rules."]}),"\n",(0,s.jsx)(t.h4,{id:"task-identifiers",children:"Task Identifiers"}),"\n",(0,s.jsxs)(t.p,{children:["A task is identified using the path to the ",(0,s.jsx)(t.code,{children:"COND"})," file where it is defined\n(relative to your project's root directory), followed by its name. For example,\na task named ",(0,s.jsx)(t.code,{children:"run_benchmark"})," defined in a ",(0,s.jsx)(t.code,{children:"COND"})," file located in\n",(0,s.jsx)(t.code,{children:"experiments/COND"})," would have the task identifier ",(0,s.jsx)(t.code,{children:"//experiments:run_benchmark"}),".\nTo have Conductor run the task, you run ",(0,s.jsx)(t.code,{children:"cond run //experiments:run_benchmark"})," in your shell."]}),"\n",(0,s.jsx)(t.h4,{id:"dependencies",children:"Dependencies"}),"\n",(0,s.jsxs)(t.p,{children:["Tasks can be dependent on other tasks. To specify a dependency, you use the\n",(0,s.jsx)(t.code,{children:"deps"})," keyword argument when defining a task.  When running a task that has\ndependencies, Conductor will ensure that all of its dependencies are executed\nfirst before the task is executed. This allows you to build a dependency graph\nof tasks, which can be used to automate your entire research computing pipeline."]}),"\n",(0,s.jsx)(t.h4,{id:"task-outputs",children:"Task Outputs"}),"\n",(0,s.jsxs)(t.p,{children:["Tasks usually (but not always) will need to produce output file(s) (e.g.,\nmeasurements, figures). When Conductor runs a task, it will set the\n",(0,s.jsx)(t.code,{children:"COND_OUT"})," environment variable to a path where the task should write its\noutputs. See the example projects for an example of how this is used. All\ntask outputs will be stored under the ",(0,s.jsx)(t.code,{children:"cond-out"})," directory."]}),"\n",(0,s.jsxs)(t.p,{children:["Similarly, Conductor will also set the ",(0,s.jsx)(t.code,{children:"COND_DEPS"})," environment variable to a\ncolon (",(0,s.jsx)(t.code,{children:":"}),") separated list of paths to the task's dependencies' outputs. If\nthe task has no dependencies, the ",(0,s.jsx)(t.code,{children:"COND_DEPS"})," environment variable will be\nset to an empty string."]}),"\n",(0,s.jsxs)(t.p,{children:["It's ",(0,s.jsx)(t.em,{children:"important"})," to write task outputs to the path specified by ",(0,s.jsx)(t.code,{children:"COND_OUT"}),".\nThis ensures other tasks can find the current task's outputs, and also allows\nConductor to archive your tasks' outputs."]})]})}function u(e={}){const{wrapper:t}={...(0,r.R)(),...e.components};return t?(0,s.jsx)(t,{...e,children:(0,s.jsx)(l,{...e})}):l(e)}},8453:(e,t,n)=>{n.d(t,{R:()=>i,x:()=>a});var s=n(6540);const r={},o=s.createContext(r);function i(e){const t=s.useContext(o);return s.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function a(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:i(e.components),s.createElement(o.Provider,{value:t},e.children)}}}]);