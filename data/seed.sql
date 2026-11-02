-- Synthetic sample data. Names and emails are invented.

INSERT INTO users (id, username, full_name, email, department, account_status, mfa_enabled, password_last_set, last_login) VALUES
 (1,  'aoconnor',  'Aoife O''Connor',   'aoife.oconnor@example.com',  'Finance',     'locked',   1, '2026-08-01', '2026-11-01'),
 (2,  'jmurphy',   'James Murphy',      'james.murphy@example.com',   'Engineering', 'active',   1, '2026-10-10', '2026-11-02'),
 (3,  'pnair',     'Priya Nair',        'priya.nair@example.com',     'Engineering', 'active',   1, '2026-09-15', '2026-11-02'),
 (4,  'tkelly',    'Tom Kelly',         'tom.kelly@example.com',      'Sales',       'active',   0, '2026-05-20', '2026-10-30'),
 (5,  'sbyrne',    'Sinead Byrne',      'sinead.byrne@example.com',   'HR',          'active',   1, '2026-10-01', '2026-11-01'),
 (6,  'rmehta',    'Rahul Mehta',       'rahul.mehta@example.com',    'Data',        'active',   1, '2026-07-12', '2026-11-02'),
 (7,  'cwalsh',    'Ciara Walsh',       'ciara.walsh@example.com',    'Marketing',   'disabled', 1, '2026-03-03', '2026-06-30'),
 (8,  'dryan',     'Declan Ryan',       'declan.ryan@example.com',    'Engineering', 'active',   1, '2026-10-20', '2026-11-02'),
 (9,  'lfernandez','Lucia Fernandez',   'lucia.fernandez@example.com','Support',     'active',   1, '2026-09-01', '2026-11-02'),
 (10, 'mdoyle',    'Mark Doyle',        'mark.doyle@example.com',     'Finance',     'active',   1, '2026-04-11', '2026-11-01'),
 (11, 'nquinn',    'Niamh Quinn',       'niamh.quinn@example.com',    'Sales',       'locked',   1, '2026-09-28', '2026-10-31'),
 (12, 'ochen',     'Oliver Chen',       'oliver.chen@example.com',    'Data',        'active',   1, '2026-10-05', '2026-11-02');

INSERT INTO tickets (id, user_id, created_at, category, priority, subject, status, resolution) VALUES
 (1,  1,  '2026-10-02', 'account_access', 'P3', 'Locked out after password change',         'resolved',  'Unlocked account; stale password cached on phone mail app'),
 (2,  1,  '2026-10-21', 'account_access', 'P3', 'Locked out again',                         'resolved',  'Unlocked; removed old credential from Windows Credential Manager'),
 (3,  2,  '2026-10-15', 'cloud_access',   'P3', 'Need read access to staging S3 bucket',    'resolved',  'Added to group dev-readonly'),
 (4,  3,  '2026-10-18', 'cloud_access',   'P2', 'AccessDenied deploying Lambda in dev',     'escalated', 'Needs lambda:UpdateFunctionCode; sent to cloud team'),
 (5,  4,  '2026-10-11', 'email',          'P4', 'Shared mailbox not showing in Outlook',    'resolved',  'Granted Full Access; restarted Outlook after automapping'),
 (6,  4,  '2026-10-29', 'security',       'P2', 'Suspicious sign-in alert',                 'escalated', 'Sent to security; MFA not enrolled'),
 (7,  5,  '2026-10-07', 'software',       'P4', 'Install request: Power BI Desktop',        'resolved',  'Deployed from company portal'),
 (8,  6,  '2026-10-12', 'network',        'P3', 'VPN disconnects every 10 minutes',         'resolved',  'Updated VPN client; disabled Wi-Fi power saving'),
 (9,  6,  '2026-10-25', 'cloud_access',   'P3', 'Cannot see Athena query results',          'resolved',  'Added to group data-analysts'),
 (10, 8,  '2026-10-22', 'hardware',       'P3', 'Laptop docking station no display',        'resolved',  'Updated dock firmware and display driver'),
 (11, 9,  '2026-10-09', 'email',          'P3', 'Emails to external domain bouncing',       'resolved',  'Recipient domain SPF issue; advised sender'),
 (12, 10, '2026-10-30', 'account_access', 'P3', 'Password expired while travelling',        'resolved',  'Self-service password reset walkthrough'),
 (13, 11, '2026-11-01', 'account_access', 'P2', 'Locked out before client demo',            'open',      NULL),
 (14, 12, '2026-10-27', 'cloud_access',   'P3', 'Request write access to prod DynamoDB',    'escalated', 'Production write needs manager and cloud team approval'),
 (15, 2,  '2026-11-01', 'outage',         'P1', 'Customer API returning 503 errors',        'escalated', 'Major incident raised; on-call engineer paged'),
 (16, 3,  '2026-10-03', 'software',       'P4', 'Docker Desktop licence prompt',            'resolved',  'Assigned licence from pool');
