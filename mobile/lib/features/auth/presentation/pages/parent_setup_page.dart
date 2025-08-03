import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/storage/models/user_preferences.dart';
import '../../../../core/theme/app_colors.dart';
import '../bloc/auth_bloc.dart';

/// Parent setup page for configuring child profile
class ParentSetupPage extends StatefulWidget {
  const ParentSetupPage({super.key});

  @override
  State<ParentSetupPage> createState() => _ParentSetupPageState();
}

class _ParentSetupPageState extends State<ParentSetupPage> {
  final _formKey = GlobalKey<FormState>();
  final _childNameController = TextEditingController();
  int _selectedAge = 6;
  int _selectedGrade = 1;
  String _selectedLearningStyle = 'visual';
  final List<String> _selectedSubjects = [];

  final List<String> _learningStyles = [
    'visual',
    'auditory',
    'kinesthetic',
    'reading',
  ];

  final List<String> _subjects = [
    'Mathematics',
    'English',
    'Science',
  ];

  @override
  void dispose() {
    _childNameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundPrimary,
      appBar: AppBar(
        title: const Text('Setup Your Child\'s Profile'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: BlocListener<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.error,
              ),
            );
          }
        },
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildWelcomeSection(),
                const SizedBox(height: 32),
                _buildChildNameField(),
                const SizedBox(height: 24),
                _buildAgeSelector(),
                const SizedBox(height: 24),
                _buildGradeSelector(),
                const SizedBox(height: 24),
                _buildLearningStyleSelector(),
                const SizedBox(height: 24),
                _buildSubjectSelector(),
                const SizedBox(height: 32),
                _buildCompleteButton(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildWelcomeSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const Icon(
              Icons.child_care,
              size: 48,
              color: AppColors.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Let\'s set up your child\'s learning profile',
              style: Theme.of(context).textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'This helps us personalize the learning experience',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChildNameField() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Child\'s Name',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _childNameController,
              decoration: const InputDecoration(
                hintText: 'Enter your child\'s name',
                prefixIcon: Icon(Icons.person_outline),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter your child\'s name';
                }
                return null;
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAgeSelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Age',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: List.generate(8, (index) {
                final age = index + 5; // Ages 5-12
                return ChoiceChip(
                  label: Text('$age'),
                  selected: _selectedAge == age,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() {
                        _selectedAge = age;
                        _selectedGrade = age - 4; // Approximate grade level
                      });
                    }
                  },
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGradeSelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Grade Level',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: List.generate(6, (index) {
                final grade = index + 1; // Grades 1-6
                return ChoiceChip(
                  label: Text('Grade $grade'),
                  selected: _selectedGrade == grade,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() {
                        _selectedGrade = grade;
                      });
                    }
                  },
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLearningStyleSelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Learning Style',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'How does your child learn best?',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: _learningStyles.map((style) {
                return ChoiceChip(
                  label: Text(style.toUpperCase()),
                  selected: _selectedLearningStyle == style,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() {
                        _selectedLearningStyle = style;
                      });
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubjectSelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Favorite Subjects',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Select subjects your child enjoys (optional)',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: _subjects.map((subject) {
                final isSelected = _selectedSubjects.contains(subject);
                return FilterChip(
                  label: Text(subject),
                  selected: isSelected,
                  onSelected: (selected) {
                    setState(() {
                      if (selected) {
                        _selectedSubjects.add(subject);
                      } else {
                        _selectedSubjects.remove(subject);
                      }
                    });
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCompleteButton() {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        final isLoading = state is AuthLoading;
        
        return SizedBox(
          height: 56,
          child: ElevatedButton(
            onPressed: isLoading ? null : _handleComplete,
            child: isLoading
                ? const CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  )
                : const Text(
                    'Complete Setup',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
          ),
        );
      },
    );
  }

  void _handleComplete() {
    if (_formKey.currentState?.validate() ?? false) {
      final authState = context.read<AuthBloc>().state;
      if (authState is AuthAuthenticated) {
        final userPreferences = UserPreferences(
          userId: authState.userId,
          childName: _childNameController.text.trim(),
          age: _selectedAge,
          gradeLevel: _selectedGrade,
          learningStyle: _selectedLearningStyle,
          favoriteSubjects: _selectedSubjects,
          lastUpdated: DateTime.now(),
        );

        context.read<AuthBloc>().add(
          AuthParentSetupCompleted(userPreferences),
        );
      }
    }
  }
}