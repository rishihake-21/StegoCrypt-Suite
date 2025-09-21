import 'package:flutter/material.dart';
import 'cyber_theme.dart';

class NotificationsPanel extends StatelessWidget {
  const NotificationsPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 300,
      decoration: CyberTheme.glassContainer,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text('Notifications', style: CyberTheme.heading2),
          ),
          const Divider(color: CyberTheme.softGray),
          Expanded(
            child: ListView(
              children: [
                _buildNotificationItem(
                  'New Feature',
                  'Hashing is now available!',
                  Icons.new_releases,
                  CyberTheme.aquaBlue,
                ),
                _buildNotificationItem(
                  'Update',
                  'UI improvements on the About page.',
                  Icons.update,
                  CyberTheme.cyberPurple,
                ),
                _buildNotificationItem(
                  'System',
                  'Welcome to StegoCrypt Suite!',
                  Icons.security,
                  CyberTheme.neonPink,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationItem(
      String title, String subtitle, IconData icon, Color color) {
    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(title, style: CyberTheme.bodyMedium),
      subtitle: Text(subtitle, style: CyberTheme.bodySmall),
    );
  }
}
