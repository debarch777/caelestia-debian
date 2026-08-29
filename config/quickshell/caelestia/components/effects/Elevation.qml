import QtQuick
import Qt5Compat.GraphicalEffects
import qs.components
import qs.services

RectangularGlow {
    property int level
    property real dp: [0, 1, 3, 6, 8, 12][level]
    property real radius: cornerRadius
    property real topLeftRadius: radius
    property real topRightRadius: radius
    property real bottomLeftRadius: radius
    property real bottomRightRadius: radius
    property var offset: ({ x: 0, y: 0 })
    property real blur: glowRadius

    cornerRadius: radius
    color: Qt.alpha(Colours.palette.m3shadow, 0.7)
    glowRadius: (dp * 5) ** 0.7
    spread: Math.max(0, -dp * 0.3 + (dp * 0.1) ** 2)

    Behavior on dp {
        Anim {
            type: Anim.SlowEffects
        }
    }
}
