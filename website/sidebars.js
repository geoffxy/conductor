module.exports = {
  docs: [
    'overview',
    {
      type: 'category',
      label: 'Reference',
      collapsible: false,
      items: [
        {
          type: 'category',
          label: 'Task Types',
          link: {type: 'doc', id: 'task-types'},
          collapsed: false,
          items: [
            'task-types/run-experiment',
            'task-types/run-command',
            'task-types/combine',
            'task-types/group',
            'task-types/run-experiment-group',
          ],
        },
        {
          type: 'category',
          label: 'Directives',
          link: {type: 'doc', id: 'directives'},
          collapsed: false,
          items: [
            'directives/include',
          ],
        },
        {
          type: 'category',
          label: 'Command Line Interface',
          link: {type: 'doc', id: 'cli'},
          collapsed: false,
          items: [
            'cli/run',
            'cli/archive',
            'cli/restore',
            'cli/where',
            'cli/clean',
            'cli/gc',
            'cli/explorer',
          ],
        },
        'configuration',
        'python-support-library',
      ],
    },
  ],
};
