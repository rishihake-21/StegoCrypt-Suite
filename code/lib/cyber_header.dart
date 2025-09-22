// cyber_header.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'cyber_theme.dart';
import 'app_provider.dart';
import 'cyber_widgets.dart';
// notifications removed

class CyberHeader extends StatefulWidget {
  const CyberHeader({super.key});

  @override
  _CyberHeaderState createState() => _CyberHeaderState();
}

class _CyberHeaderState extends State<CyberHeader>
    with TickerProviderStateMixin {
  late AnimationController _glowController;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _glowController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat(reverse: true);

    _glowAnimation = Tween<double>(begin: 0.3, end: 1.0).animate(
      CurvedAnimation(parent: _glowController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _glowController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
  final appProvider = Provider.of<AppProvider>(context);
  final bool isDarkMode = appProvider.isDarkMode;

    return Container(
      height: 80,
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
      decoration: BoxDecoration(
        color: CyberTheme.glassFillFor(context),
        border: Border(
          bottom: BorderSide(
            color: CyberTheme.subtleBorderFor(context).withOpacity(0.1),
            width: 1,
          ),
        ),
      ),
      child:
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Expanded(child: Container()),

            // Theme Toggle - pill style
            _PillThemeToggle(
              isDarkMode: isDarkMode,
              onToggle: appProvider.toggleThemeMode,
              glowAnimation: _glowAnimation,
            ),

            const SizedBox(width: 16),

            // Notifications removed

            const SizedBox(width: 8),

            // // User Profile
            // Consumer<AppProvider>(
            //   builder: (context, appProvider, child) {
            //     return Material(
            //       color: Colors.transparent,
            //       borderRadius: BorderRadius.circular(24),
            //       child: InkWell(
            //         borderRadius: BorderRadius.circular(24),
            //         onTap: () {
            //           // Handle profile tap
            //         },
            //         child: Container(
            //           padding: const EdgeInsets.all(8),
            //           decoration: BoxDecoration(
            //             borderRadius: BorderRadius.circular(24),
            //             border: Border.all(
            //               color: CyberTheme.glowWhite.withOpacity(0.2),
            //             ),
            //           ),
            //           child: Row(
            //             children: [
            //               Container(
            //                 width: 32,
            //                 height: 32,
            //                 decoration: BoxDecoration(
            //                   shape: BoxShape.circle,
            //                   gradient: CyberTheme.primaryGradient,
            //                 ),
            //                 child: const Icon(
            //                   Icons.person_outline,
            //                   size: 16,
            //                   color: Colors.white,
            //                 ),
            //               ),
            //               const SizedBox(width: 12),
            //               const Column(
            //                 crossAxisAlignment: CrossAxisAlignment.start,
            //                 mainAxisSize: MainAxisSize.min,
            //                 children: [
            //                   Text(
            //                     'Cyber Agent',
            //                     style: TextStyle(
            //                       fontSize: 12,
            //                       fontWeight: FontWeight.w600,
            //                       color: Colors.white,
            //                     ),
            //                   ),
            //                   Text(
            //                     'Admin Access',
            //                     style: TextStyle(
            //                       fontSize: 10,
            //                       color: CyberTheme.aquaBlue,
            //                     ),
            //                   ),
            //                 ],
            //               ),
            //               const SizedBox(width: 8),
            //               const Icon(
            //                 Icons.arrow_drop_down_outlined,
            //                 size: 16,
            //                 color: CyberTheme.softGray,
            //               ),
            //             ],
            //           ),
            //         ),
            //       ),
            //     );
            //   },
            // ),
          ],
        )
    );
  }

  Widget _buildQuickActionButton({
    required IconData icon,
    int? badgeCount,
    required VoidCallback onPressed,
  }) {
    return Stack(
      children: [
        Material(
          color: Colors.transparent,
          shape: const CircleBorder(),
          child: InkWell(
            borderRadius: BorderRadius.circular(24),
            onTap: onPressed,
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: CyberTheme.glassWhite,
              ),
              child: Icon(icon, size: 18, color: Colors.white),
            ),
          ),
        ),
        if (badgeCount != null && badgeCount > 0)
          Positioned(
            right: 0,
            top: 0,
            child: Container(
              width: 16,
              height: 16,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: CyberTheme.primaryGradient,
              ),
              child: Center(
                child: Text(
                  badgeCount.toString(),
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _PillThemeToggle extends StatelessWidget {
  final bool isDarkMode;
  final VoidCallback onToggle;
  final Animation<double> glowAnimation;

  const _PillThemeToggle({
    required this.isDarkMode,
    required this.onToggle,
    required this.glowAnimation,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: glowAnimation,
      builder: (context, child) {
        return Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(24),
          child: InkWell(
            borderRadius: BorderRadius.circular(24),
            onTap: onToggle,
            child: Container(
              width: 72,
              height: 36,
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(24),
                color: isDarkMode ? CyberTheme.deepViolet : Colors.white,
                boxShadow: isDarkMode
                    ? [
                        BoxShadow(
                          color: CyberTheme.aquaBlue.withOpacity(
                            glowAnimation.value * 0.3,
                          ),
                          blurRadius: 14,
                          spreadRadius: 1,
                        ),
                      ]
                    : [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.06),
                          blurRadius: 10,
                          spreadRadius: 1,
                        ),
                      ],
                border: Border.all(
                  color: CyberTheme.subtleBorderFor(context).withOpacity(0.2),
                ),
              ),
              child: Stack(
                children: [
                  Align(
                    alignment: isDarkMode
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: isDarkMode
                            ? CyberTheme.primaryGradient
                            : LinearGradient(
                                colors: [
                                  Colors.orangeAccent,
                                  Colors.yellow.shade600,
                                ],
                              ),
                        boxShadow: [
                          BoxShadow(
                            color: (isDarkMode
                                    ? CyberTheme.cyberPurple
                                    : Colors.orange)
                                .withOpacity(0.3),
                            blurRadius: 8,
                            spreadRadius: 1,
                          ),
                        ],
                      ),
                      child: Icon(
                        isDarkMode
                            ? Icons.dark_mode_outlined
                            : Icons.light_mode_outlined,
                        size: 16,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
