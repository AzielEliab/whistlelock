import 'package:flutter/material.dart';

/// Paper and charcoal surfaces. Gold focus. Follows the system theme.
const Color kMatteBlack = Color(0xFF0B0B0B);
const Color kSurface = Color(0xFF141414);
const Color kGold = Color(0xFFC9A227);
const Color kGoldDim = Color(0xFF8A7219);
const Color kIvory = Color(0xFFE8E0D0);

ButtonStyle _goldFocus() {
  return ButtonStyle(
    side: WidgetStateProperty.resolveWith((states) {
      if (states.contains(WidgetState.focused)) {
        return const BorderSide(color: kGold, width: 3);
      }
      return null;
    }),
  );
}

ThemeData _base(ColorScheme scheme, Color scaffold) {
  return ThemeData(
    useMaterial3: true,
    brightness: scheme.brightness,
    colorScheme: scheme,
    scaffoldBackgroundColor: scaffold,
    focusColor: kGold,
    appBarTheme: AppBarTheme(
      backgroundColor: scaffold,
      foregroundColor: scheme.onSurface,
      elevation: 0,
      centerTitle: false,
    ),
    filledButtonTheme: FilledButtonThemeData(style: _goldFocus()),
    outlinedButtonTheme: OutlinedButtonThemeData(style: _goldFocus()),
    textButtonTheme: TextButtonThemeData(style: _goldFocus()),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: scheme.brightness == Brightness.dark
          ? const Color(0xFF1A1A1A)
          : const Color(0xFFFFFDF8),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: kGold, width: 2),
      ),
    ),
  );
}

ThemeData buildLightTheme() {
  const scheme = ColorScheme.light(
    primary: kGold,
    onPrimary: Color(0xFF1A1408),
    secondary: kGoldDim,
    onSecondary: Color(0xFF1C1915),
    surface: Color(0xFFF7F4EE),
    onSurface: Color(0xFF1C1915),
    error: Color(0xFF9D2C2C),
    onError: Color(0xFFFFFDF8),
  );
  return _base(scheme, const Color(0xFFF7F4EE));
}

ThemeData buildDarkTheme() {
  const scheme = ColorScheme.dark(
    brightness: Brightness.dark,
    primary: kGold,
    onPrimary: kMatteBlack,
    secondary: kGoldDim,
    onSecondary: kIvory,
    surface: kSurface,
    onSurface: kIvory,
    error: Color(0xFFB54A4A),
    onError: kIvory,
  );
  return _base(scheme, kMatteBlack);
}
