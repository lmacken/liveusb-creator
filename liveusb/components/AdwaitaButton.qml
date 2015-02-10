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
            Component.onCompleted: {
                if (root.color != palette.button)
                    gradient = emptyGrad
            }
            Gradient {
                id: emptyGrad
            }
        }
        label: Text {
            color: root.textColor
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: control.text
        }
    }
}

