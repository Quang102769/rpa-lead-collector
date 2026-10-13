// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // Tính năng mới
        'fix',      // Sửa lỗi
        'docs',     // Cập nhật tài liệu
        'style',    // Format code (không ảnh hưởng logic)
        'refactor', // Tái cấu trúc mã nguồn
        'perf',     // Tối ưu hiệu năng
        'test',     // Viết test
        'build',    // Thay đổi build/dependencies
        'ci',       // Cấu hình CI/CD
        'chore',    // Việc linh tinh (cấu hình, tool)
        'revert',   // Revert commit trước đó
      ],
    ],
    'subject-case': [2, 'never', ['start-case', 'pascal-case', 'upper-case']],
    'subject-full-stop': [2, 'never', '.'],
  },
};
