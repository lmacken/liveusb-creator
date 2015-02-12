import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

Button {
    id: root
    property color color: palette.button
    property color textColor: palette.buttonText

    style: ButtonStyle {
        background: AdwaitaRectangle {
            color: root.color
            border.color: control.enabled ? "#777777" : "#c2c2c2"
        }
        label: Text {
            color: control.enabled ? root.textColor : "gray"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: control.text
        }
    }
}

