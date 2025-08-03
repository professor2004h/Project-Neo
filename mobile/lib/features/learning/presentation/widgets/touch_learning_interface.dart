import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Touch-friendly learning interface with gesture support
class TouchLearningInterface extends StatefulWidget {
  final Widget child;
  final VoidCallback? onSwipeLeft;
  final VoidCallback? onSwipeRight;
  final VoidCallback? onSwipeUp;
  final VoidCallback? onSwipeDown;
  final VoidCallback? onDoubleTap;
  final VoidCallback? onLongPress;
  final Function(ScaleUpdateDetails)? onScale;
  final bool enableHapticFeedback;
  final double swipeThreshold;

  const TouchLearningInterface({
    super.key,
    required this.child,
    this.onSwipeLeft,
    this.onSwipeRight,
    this.onSwipeUp,
    this.onSwipeDown,
    this.onDoubleTap,
    this.onLongPress,
    this.onScale,
    this.enableHapticFeedback = true,
    this.swipeThreshold = 100.0,
  });

  @override
  State<TouchLearningInterface> createState() => _TouchLearningInterfaceState();
}

class _TouchLearningInterfaceState extends State<TouchLearningInterface>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late AnimationController _slideController;
  late Animation<double> _scaleAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _slideController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.95,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.easeInOut,
    ));

    _slideAnimation = Tween<Offset>(
      begin: Offset.zero,
      end: const Offset(0.1, 0),
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.elasticOut,
    ));
  }

  @override
  void dispose() {
    _scaleController.dispose();
    _slideController.dispose();
    super.dispose();
  }

  void _triggerHapticFeedback() {
    if (widget.enableHapticFeedback) {
      HapticFeedback.lightImpact();
    }
  }

  void _handleTapDown(TapDownDetails details) {
    _scaleController.forward();
    _triggerHapticFeedback();
  }

  void _handleTapUp(TapUpDetails details) {
    _scaleController.reverse();
  }

  void _handleTapCancel() {
    _scaleController.reverse();
  }

  void _handlePanEnd(DragEndDetails details) {
    final velocity = details.velocity.pixelsPerSecond;
    final dx = velocity.dx.abs();
    final dy = velocity.dy.abs();

    if (dx > widget.swipeThreshold || dy > widget.swipeThreshold) {
      _triggerHapticFeedback();

      if (dx > dy) {
        // Horizontal swipe
        if (velocity.dx > 0) {
          widget.onSwipeRight?.call();
          _slideController.forward().then((_) => _slideController.reverse());
        } else {
          widget.onSwipeLeft?.call();
          _slideController.forward().then((_) => _slideController.reverse());
        }
      } else {
        // Vertical swipe
        if (velocity.dy > 0) {
          widget.onSwipeDown?.call();
        } else {
          widget.onSwipeUp?.call();
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: _handleTapDown,
      onTapUp: _handleTapUp,
      onTapCancel: _handleTapCancel,
      onDoubleTap: () {
        _triggerHapticFeedback();
        widget.onDoubleTap?.call();
      },
      onLongPress: () {
        HapticFeedback.mediumImpact();
        widget.onLongPress?.call();
      },
      onPanEnd: _handlePanEnd,
      onScaleUpdate: widget.onScale,
      child: AnimatedBuilder(
        animation: Listenable.merge([_scaleController, _slideController]),
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: SlideTransition(
              position: _slideAnimation,
              child: widget.child,
            ),
          );
        },
      ),
    );
  }
}

/// Interactive learning card with touch gestures
class InteractiveLearningCard extends StatefulWidget {
  final String title;
  final String content;
  final Widget? image;
  final VoidCallback? onTap;
  final VoidCallback? onSwipeLeft;
  final VoidCallback? onSwipeRight;
  final Color? backgroundColor;
  final bool isCompleted;

  const InteractiveLearningCard({
    super.key,
    required this.title,
    required this.content,
    this.image,
    this.onTap,
    this.onSwipeLeft,
    this.onSwipeRight,
    this.backgroundColor,
    this.isCompleted = false,
  });

  @override
  State<InteractiveLearningCard> createState() => _InteractiveLearningCardState();
}

class _InteractiveLearningCardState extends State<InteractiveLearningCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _flipAnimation;
  bool _isFlipped = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _flipAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _flip() {
    if (_isFlipped) {
      _controller.reverse();
    } else {
      _controller.forward();
    }
    setState(() {
      _isFlipped = !_isFlipped;
    });
  }

  @override
  Widget build(BuildContext context) {
    return TouchLearningInterface(
      onDoubleTap: _flip,
      onSwipeLeft: widget.onSwipeLeft,
      onSwipeRight: widget.onSwipeRight,
      child: AnimatedBuilder(
        animation: _flipAnimation,
        builder: (context, child) {
          final isShowingFront = _flipAnimation.value < 0.5;
          return Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.001)
              ..rotateY(_flipAnimation.value * 3.14159),
            child: Card(
              elevation: 8,
              color: widget.backgroundColor ?? Theme.of(context).cardColor,
              child: Container(
                padding: const EdgeInsets.all(16),
                child: isShowingFront ? _buildFront() : _buildBack(),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildFront() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                widget.title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            if (widget.isCompleted)
              const Icon(
                Icons.check_circle,
                color: Colors.green,
                size: 24,
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (widget.image != null) ...[
          Center(child: widget.image!),
          const SizedBox(height: 12),
        ],
        Text(
          widget.content,
          style: const TextStyle(fontSize: 16),
        ),
        const SizedBox(height: 16),
        const Center(
          child: Text(
            'Double tap to flip • Swipe to navigate',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBack() {
    return Transform(
      alignment: Alignment.center,
      transform: Matrix4.identity()..rotateY(3.14159),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.lightbulb_outline,
            size: 48,
            color: Colors.orange,
          ),
          const SizedBox(height: 16),
          const Text(
            'Additional Information',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'This is the back of the card with additional learning content and tips.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Double tap to flip back',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}

/// Draggable learning element for interactive exercises
class DraggableLearningElement extends StatefulWidget {
  final String id;
  final Widget child;
  final String? targetId;
  final VoidCallback? onDragStarted;
  final VoidCallback? onDragEnd;
  final Function(String targetId)? onAccepted;

  const DraggableLearningElement({
    super.key,
    required this.id,
    required this.child,
    this.targetId,
    this.onDragStarted,
    this.onDragEnd,
    this.onAccepted,
  });

  @override
  State<DraggableLearningElement> createState() => _DraggableLearningElementState();
}

class _DraggableLearningElementState extends State<DraggableLearningElement> {
  bool _isDragging = false;

  @override
  Widget build(BuildContext context) {
    return Draggable<String>(
      data: widget.id,
      feedback: Material(
        elevation: 8,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Theme.of(context).primaryColor.withOpacity(0.8),
            borderRadius: BorderRadius.circular(8),
          ),
          child: widget.child,
        ),
      ),
      childWhenDragging: Opacity(
        opacity: 0.5,
        child: widget.child,
      ),
      onDragStarted: () {
        setState(() {
          _isDragging = true;
        });
        HapticFeedback.mediumImpact();
        widget.onDragStarted?.call();
      },
      onDragEnd: (details) {
        setState(() {
          _isDragging = false;
        });
        widget.onDragEnd?.call();
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        transform: Matrix4.identity()..scale(_isDragging ? 1.1 : 1.0),
        child: widget.child,
      ),
    );
  }
}

/// Drop target for draggable elements
class LearningDropTarget extends StatefulWidget {
  final String id;
  final Widget child;
  final Function(String draggedId)? onAccept;
  final bool isCorrectTarget;

  const LearningDropTarget({
    super.key,
    required this.id,
    required this.child,
    this.onAccept,
    this.isCorrectTarget = false,
  });

  @override
  State<LearningDropTarget> createState() => _LearningDropTargetState();
}

class _LearningDropTargetState extends State<LearningDropTarget> {
  bool _isHovering = false;

  @override
  Widget build(BuildContext context) {
    return DragTarget<String>(
      onWillAccept: (data) => true,
      onAccept: (data) {
        HapticFeedback.heavyImpact();
        widget.onAccept?.call(data);
      },
      onMove: (details) {
        if (!_isHovering) {
          setState(() {
            _isHovering = true;
          });
          HapticFeedback.selectionClick();
        }
      },
      onLeave: (data) {
        setState(() {
          _isHovering = false;
        });
      },
      builder: (context, candidateData, rejectedData) {
        return AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          decoration: BoxDecoration(
            border: Border.all(
              color: _isHovering
                  ? (widget.isCorrectTarget ? Colors.green : Colors.orange)
                  : Colors.transparent,
              width: 2,
            ),
            borderRadius: BorderRadius.circular(8),
          ),
          child: widget.child,
        );
      },
    );
  }
}